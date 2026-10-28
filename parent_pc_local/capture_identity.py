"""Identify a completed Parent PC capture without changing its audio bytes."""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
import wave


def capture_identity(wav_path: Path) -> dict:
    """Return identity only for a finalized, complete, nonempty PCM WAV.

    The first Analyze operation can then use the existing protected saved-WAV
    route. This function never creates another audio file or edits metadata.
    """
    path = Path(wav_path)
    raw = path.read_bytes()
    try:
        with wave.open(io.BytesIO(raw), "rb") as audio:
            expected = audio.getnframes() * audio.getnchannels() * audio.getsampwidth()
            if not expected or len(audio.readframes(audio.getnframes())) != expected:
                raise ValueError("incomplete_pcm_capture")
    except (EOFError, wave.Error) as exc:
        raise ValueError("invalid_pcm_capture") from exc
    return {
        "recordingId": path.stem,
        "audioSha256": hashlib.sha256(raw).hexdigest(),
        "audioBytes": len(raw),
        "originalAudioImmutable": True,
        "captureIdentityVersion": "parent-pc-capture-sha256-v1",
    }
