"""Pre-build native-library smoke test; fails the build if unavailable."""
import io
import numpy as np
import soundfile as sf
import av
import ctranslate2
import faster_whisper
buf = io.BytesIO()
sf.write(buf, np.zeros(16000, dtype=np.float32), 16000, format="WAV")
buf.seek(0)
with av.open(buf, mode="r", format="wav") as container:
    assert next(container.decode(audio=0)).samples > 0
print("PyAV WAV decode and Faster-Whisper native imports: PASS")
