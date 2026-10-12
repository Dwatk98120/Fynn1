from __future__ import annotations
import math, wave
from pathlib import Path

def _rms(values):
    return math.sqrt(sum(float(v)*float(v) for v in values)/len(values)) if values else 0.0

def analyze_temporal_prosody(path: str | Path) -> dict:
    path = Path(path)
    try:
        with wave.open(str(path), "rb") as wav:
            channels = wav.getnchannels()
            width = wav.getsampwidth()
            rate = wav.getframerate()
            frames = wav.getnframes()
            raw = wav.readframes(frames)
        if width != 2 or not raw or rate <= 0:
            return {"available": False, "reason": "unsupported_or_empty_audio"}

        import array
        samples = array.array("h")
        samples.frombytes(raw)
        if channels > 1:
            samples = array.array("h", samples[::channels])
        samples = [int(x) for x in samples]
        duration = len(samples) / float(rate)
        if duration <= 0:
            return {"available": False, "reason": "empty_audio"}

        window = max(1, int(rate * 0.020))
        frame_rms = [_rms(samples[i:i+window]) for i in range(0, len(samples), window) if samples[i:i+window]]
        if not frame_rms:
            return {"available": False, "reason": "no_frames"}

        peak_rms = max(frame_rms) or 1.0
        threshold = max(220.0, peak_rms * 0.10)
        voiced = [v >= threshold for v in frame_rms]

        pauses, run = [], None
        for idx, is_voiced in enumerate(voiced):
            if not is_voiced and run is None:
                run = idx
            elif is_voiced and run is not None:
                pauses.append((idx-run)*0.020)
                run = None
        if run is not None:
            pauses.append((len(voiced)-run)*0.020)

        internal = list(pauses)
        if internal and not voiced[0]:
            internal = internal[1:]
        if internal and not voiced[-1]:
            internal = internal[:-1]

        meaningful = [p for p in internal if p >= 0.12]
        avg_pause = sum(meaningful)/len(meaningful) if meaningful else 0.0
        longest = max(meaningful) if meaningful else 0.0

        voiced_duration = sum(1 for v in voiced if v) * 0.020
        silence_duration = max(0.0, duration - voiced_duration)

        energy = [v/peak_rms for v in frame_rms]
        peaks = []
        for i in range(1, len(energy)-1):
            if energy[i] >= 0.28 and energy[i] > energy[i-1] and energy[i] >= energy[i+1]:
                if not peaks or (i-peaks[-1]) >= 5:
                    peaks.append(i)

        sps = len(peaks)/duration if duration > 0 else 0.0
        strengths = [energy[i] for i in peaks]
        stress_pattern = []
        if strengths:
            mean_s = sum(strengths)/len(strengths)
            for idx, val in zip(peaks, strengths):
                stress_pattern.append({
                    "timeSeconds": round(idx*0.020,3),
                    "relativeStrength": round(val,3),
                    "stress": "strong" if val >= mean_s*1.15 else "weak" if val <= mean_s*0.80 else "moderate"
                })

        intervals = [(b-a)*0.020 for a,b in zip(peaks, peaks[1:])]
        rhythm = None
        if len(intervals) >= 2:
            mean_i = sum(intervals)/len(intervals)
            std_i = math.sqrt(sum((x-mean_i)**2 for x in intervals)/len(intervals))
            rhythm = max(0.0, min(1.0, 1.0-(std_i/max(mean_i,1e-6))))

        tail_frames = max(1, int(0.18/0.020))
        tail = energy[-tail_frames:]
        prior = energy[-2*tail_frames:-tail_frames] if len(energy) >= 2*tail_frames else energy[:-tail_frames]
        tail_energy = sum(tail)/len(tail) if tail else 0.0
        prior_energy = sum(prior)/len(prior) if prior else tail_energy
        drop = max(-1.0, min(1.0, prior_energy-tail_energy))
        ending = "strong_finish" if tail_energy >= 0.45 else "soft_finish" if tail_energy >= 0.20 else "trailing_or_silent_finish"

        rate_band = "fast" if sps >= 5.0 else "moderate" if sps >= 2.0 else "slow" if sps > 0 else "unknown"

        return {
            "available": True,
            "durationSeconds": round(duration,3),
            "voicedDurationSeconds": round(voiced_duration,3),
            "silenceDurationSeconds": round(silence_duration,3),
            "pauseCount": len(meaningful),
            "averagePauseSeconds": round(avg_pause,3),
            "longestPauseSeconds": round(longest,3),
            "estimatedSyllablePeaks": len(peaks),
            "syllablesPerSecond": round(sps,3),
            "speechRateBand": rate_band,
            "stressPattern": stress_pattern[:12],
            "rhythmConsistency": round(rhythm,3) if rhythm is not None else None,
            "endOfUtterance": {
                "pattern": ending,
                "tailEnergy": round(tail_energy,3),
                "priorEnergy": round(prior_energy,3),
                "tailEnergyDrop": round(drop,3),
            },
            "notes": [
                "Timing/prosody values are observational evidence.",
                "Stress and syllable counts are approximate and are not clinical measurements."
            ]
        }
    except Exception as exc:
        return {"available": False, "reason": "temporal_prosody_analysis_failed", "detail": str(exc)}
