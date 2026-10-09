import numpy as np

def rms(x):
    x = np.asarray(x, dtype=np.float32)
    return float(np.sqrt(np.mean(np.square(x))) + 1e-9)

def acoustic_features(samples, sr=16000):
    """Lightweight acoustic evidence. This is heuristic evidence, not a clinical measure."""
    x = np.asarray(samples, dtype=np.float32)
    if x.size == 0:
        return {"durationSec": 0.0, "rms": 0.0, "finalEnergyRatio": 0.0,
                "finalSilenceRatio": 0.0, "peakRatio": 0.0}
    n = len(x)
    tail_n = max(int(sr * 0.12), 1)
    tail = x[-min(tail_n, n):]
    body = x[:-min(tail_n, n)] if n > tail_n else x
    body_rms = rms(body)
    tail_rms = rms(tail)
    threshold = max(body_rms * 0.18, 0.004)
    return {
        "durationSec": round(n / sr, 3),
        "rms": round(rms(x), 6),
        "finalEnergyRatio": round(min(tail_rms / max(body_rms, 1e-6), 2.0), 3),
        "finalSilenceRatio": round(float(np.mean(np.abs(tail) < threshold)), 3),
        "peakRatio": round(float(np.max(np.abs(tail)) / max(np.max(np.abs(x)), 1e-6)), 3),
    }

def temporal_features(samples, sr=16000):
    x = np.asarray(samples, dtype=np.float32)
    if x.size < 2:
        return {"tailChange": 0.0, "tailWindowMs": 0}
    tail_n = max(int(sr * 0.08), 2)
    tail = x[-min(tail_n, len(x)):]
    half = max(len(tail)//2, 1)
    a, b = tail[:half], tail[half:]
    a_r, b_r = rms(a), rms(b)
    return {
        "tailChange": round(float(abs(b_r-a_r) / max(a_r, 1e-6)), 3),
        "tailWindowMs": round(len(tail) * 1000 / sr, 1)
    }

def evidence_scores(acoustic, temporal, observed, candidate):
    """Combines model/phoneme evidence with simple acoustic/temporal evidence."""
    observed_tokens = max(len(observed), 1)
    phoneme_evidence = min(0.98, 0.45 + 0.05 * observed_tokens)
    # A clear energy transition or low-energy tail can support a boundary,
    # but neither is treated as proof of a consonant or deletion.
    boundary = min(1.0, 0.35 + 0.45 * min(acoustic.get("tailChange", 0.0), 1.0))
    if candidate.get("possibleFinalOmission"):
        acoustic_evidence = min(0.95, 0.45 + 0.35 * acoustic.get("finalSilenceRatio", 0.0))
    else:
        acoustic_evidence = min(0.95, 0.55 + 0.25 * acoustic.get("peakRatio", 0.0))
    temporal_evidence = min(0.95, 0.5 + 0.4 * boundary)
    return {
        "phoneme": round(phoneme_evidence, 3),
        "acoustic": round(acoustic_evidence, 3),
        "temporal": round(temporal_evidence, 3),
    }

def combined_confidence(evidence, context_boost=0.0):
    # Deliberately conservative: this is a candidate-ranking confidence,
    # not a clinical confidence score.
    base = (
        0.50 * evidence.get("phoneme", 0.0) +
        0.30 * evidence.get("acoustic", 0.0) +
        0.20 * evidence.get("temporal", 0.0)
    )
    return round(max(0.0, min(0.99, base + min(context_boost, 0.08))), 3)
