"""Fetch and validate offline Faster-Whisper model during BUILD only."""
from pathlib import Path
from huggingface_hub import snapshot_download
root = Path(__file__).resolve().parents[1]
target = root / "models" / "faster-whisper-base.en"
target.mkdir(parents=True, exist_ok=True)
print("Fetching Systran/faster-whisper-base.en into", target)
snapshot_download(repo_id="Systran/faster-whisper-base.en", local_dir=str(target))
for name in ("model.bin", "config.json", "tokenizer.json"):
    file = target / name
    if not file.is_file() or file.stat().st_size == 0:
        raise SystemExit("Missing/empty offline model asset: " + str(file))
print("Offline model assets verified")
