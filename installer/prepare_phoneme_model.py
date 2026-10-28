"""Stage the independent phoneme recognizer into the Windows offline installer.

Run at BUILD time, never when the installed Parent PC is analyzing audio.
"""
from pathlib import Path
from transformers import AutoProcessor, AutoModelForCTC

REPO = "speech31/wav2vec2-large-english-phoneme-v2"
DEST = Path("models/phoneme-wav2vec2")


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    if (DEST / "config.json").is_file() and any(
        (DEST / name).is_file() for name in ("model.safetensors", "pytorch_model.bin")
    ):
        # Still verify tokenizer assets are complete.
        AutoProcessor.from_pretrained(str(DEST), local_files_only=True)
        print("Phoneme offline model already staged and tokenizer verified.")
        return
    print("Preparing offline phoneme model for Windows installer (large download).", flush=True)
    processor = AutoProcessor.from_pretrained(REPO)
    model = AutoModelForCTC.from_pretrained(REPO)
    processor.save_pretrained(str(DEST))
    model.save_pretrained(str(DEST), safe_serialization=True)
    AutoProcessor.from_pretrained(str(DEST), local_files_only=True)
    print("Offline phoneme model staged at", DEST.resolve(), flush=True)


if __name__ == "__main__":
    main()
