from __future__ import annotations

import math
import wave
from pathlib import Path


def analyze_wav_quality(path: str | Path) -> dict:
    path = Path(path)
    try:
        with wave.open(str(path), "rb") as wav:
            channels = wav.getnchannels()
            sampwidth = wav.getsampwidth()
            rate = wav.getframerate()
            frames = wav.getnframes()
            raw = wav.readframes(frames)

        if sampwidth != 2 or not raw:
            return {
                "usable": False,
                "score": 0.0,
                "label": "poor",
                "issues": ["unsupported_or_empty_audio"],
                "metrics": {}
            }

        import array
        samples = array.array("h")
        samples.frombytes(raw)

        if channels > 1:
            samples = array.array("h", samples[::channels])

        count = max(1, len(samples))
        duration = count / float(rate or 1)
        abs_vals = [abs(int(x)) for x in samples]

        max_pcm = 32767.0
        peak = max(abs_vals) if abs_vals else 0
        rms = math.sqrt(sum(float(x) * float(x) for x in samples) / count) if samples else 0.0
        peak_ratio = peak / max_pcm
        rms_ratio = rms / max_pcm

        silence_threshold = 350
        silence_ratio = sum(1 for x in abs_vals if x < silence_threshold) / count

        clipping_threshold = int(max_pcm * 0.98)
        clipping_ratio = sum(1 for x in abs_vals if x >= clipping_threshold) / count

        score = 100.0

        if duration < 0.35:
            score -= 35
        elif duration < 0.75:
            score -= 15

        if rms_ratio < 0.008:
            score -= 35
        elif rms_ratio < 0.02:
            score -= 15

        if silence_ratio > 0.92:
            score -= 40
        elif silence_ratio > 0.78:
            score -= 18

        if clipping_ratio > 0.03:
            score -= 30
        elif clipping_ratio > 0.005:
            score -= 12

        score = max(0.0, min(100.0, score))
        usable = score >= 45.0

        if score >= 80:
            label = "good"
        elif score >= 60:
            label = "fair"
        elif score >= 45:
            label = "marginal"
        else:
            label = "poor"

        issues = []
        if duration < 0.35:
            issues.append("recording_too_short")
        if rms_ratio < 0.008:
            issues.append("very_low_volume")
        elif rms_ratio < 0.02:
            issues.append("low_volume")
        if silence_ratio > 0.92:
            issues.append("mostly_silence")
        elif silence_ratio > 0.78:
            issues.append("high_silence")
        if clipping_ratio > 0.03:
            issues.append("heavy_clipping")
        elif clipping_ratio > 0.005:
            issues.append("some_clipping")

        return {
            "usable": usable,
            "score": round(score / 100.0, 3),
            "label": label,
            "issues": issues,
            "metrics": {
                "durationSeconds": round(duration, 3),
                "sampleRate": rate,
                "peakRatio": round(peak_ratio, 4),
                "rmsRatio": round(rms_ratio, 4),
                "silenceRatio": round(silence_ratio, 4),
                "clippingRatio": round(clipping_ratio, 4),
            },
        }
    except Exception as exc:
        return {
            "usable": False,
            "score": 0.0,
            "label": "unknown",
            "issues": ["quality_analysis_failed"],
            "reason": str(exc),
            "metrics": {}
        }
