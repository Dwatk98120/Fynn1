"""Fail a Windows build if bundled Silero VAD cannot run fully offline."""
import torch
from silero_vad import load_silero_vad, get_speech_timestamps

model = load_silero_vad()
assert model is not None, "Silero model asset missing"
with torch.inference_mode():
    intervals = get_speech_timestamps(
        torch.zeros(16000, dtype=torch.float32),
        model,
        sampling_rate=16000,
        return_seconds=True,
    )
assert isinstance(intervals, list), "Silero inference did not return intervals"
print("Silero VAD bundled model and offline inference: PASS")
