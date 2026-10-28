"""Fail closed when an Inno Setup retry would package an old Parent PC EXE.

The full build performs its frozen-code self-check, then stamps exactly the
executable and source it tested. COMPILE_INSTALLER_ONLY validates that stamp.
Only SHA-256 digests of program files are recorded, never caregiver data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RELEASE_MARKER = "layer2-background-vocal-review-v1"
MANIFEST_PATH = Path("dist/HearliumParentPC/layer2_build_integrity.json")
TRACKED_PATHS = (
    "dist/HearliumParentPC/HearliumParentPC.exe",
    "server/analysis_engine.py",
    "server/speech_activity_review.py",
    "server/phoneme_timing_review.py",
    "server/android_recording_storage.py",
    "server/analysis_jobs.py",
    "server/main.py",
    "parent_pc_local/hearlium_launcher.py",
    "parent_pc_local/direct_recording.py",
    "parent_pc_local/reanalysis_integrity.py",
    "parent_pc_local/upload_retry_check.py",
    "parent_pc_local/speech_hotfix_checks.py",
    "parent_pc_local/hearlium_parent_pc_gui.py",
    "server/reference_audio.py",
    "parent_pc_local/reference_audio_gui.py",
    "server/temporal_prosody.py",
    "server/utterance_prosody_review.py",
    "server/phoneme_substitution.py",
    "server/review_vocabulary.py",
    "server/candidate_word_engine.py",
    "server/word_asr.py",
    "server/recognition_diagnostics.py",
    "server/layer_health.py",
    "HearliumParentPC.spec",
    "installer/verify_layer2_build.py",
    "parent_pc_local/gui_smoke_check.py",
    "installer/verify_tk_build.py",
    "installer/verify_frozen_gui.py",
    "server/ctc_segmentation.py",
    "server/reference_phoneme_alignment.py",
    "server/word_phoneme_alignment_review.py",
    "parent_pc_local/capture_identity.py",
    "parent_pc_local/phoneme_alignment_client.py",
    "parent_pc_local/phoneme_hotfix_checks.py",
    "installer/verify_phoneme_build.py",
    "parent_pc_local/legacy_alias_checks.py",
    "installer/verify_legacy_alias_build.py",
    "installer/verify_0421_archive.py",
    "server/nltk_resources.py",
    "installer/prepare_nltk_data.py",
    "server/pc_copy_verification.py",
)


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _snapshot(root: Path) -> dict[str, str]:
    digests = {}
    for rel in TRACKED_PATHS:
        path = root / rel
        if not path.is_file() or not path.stat().st_size:
            raise RuntimeError(f"Required build file missing or empty: {rel}")
        digests[rel] = _digest(path)
    if "layer2-activity-tail-v2" not in (root / "server/analysis_engine.py").read_text(encoding="utf-8"):
        raise RuntimeError("This source is missing the required Layer 2 evidence version")
    if "layer2-speech-ambient-crosscheck-v1" not in (root / "server/speech_activity_review.py").read_text(encoding="utf-8"):
        raise RuntimeError("This source is missing the speech-versus-ambient cross-check")
    if "layer2-target-speaker-attribution-v1" not in (root / "server/speech_activity_review.py").read_text(encoding="utf-8"):
        raise RuntimeError("This source is missing the target-speaker attribution warning")
    if "layer23-boundary-phoneme-reliability-v1" not in (root / "server/phoneme_timing_review.py").read_text(encoding="utf-8"):
        raise RuntimeError("This source is missing the Layer 2/3 phoneme timing review")
    if "layer2-post-word-energy-review-v1" not in (root / "server/phoneme_timing_review.py").read_text(encoding="utf-8"):
        raise RuntimeError("This source is missing the post-word energy diagnostic")
    if RELEASE_MARKER not in (root / "parent_pc_local/direct_recording.py").read_text(encoding="utf-8"):
        raise RuntimeError("This source is missing Parent PC source/review display protections")
    if "recording_source=\"android\"" not in (root / "server/main.py").read_text(encoding="utf-8"):
        raise RuntimeError("This source is missing the recording-source contract")
    return digests


def _verify_gui(root: Path) -> None:
    subprocess.run([sys.executable, str(root / "installer/verify_frozen_gui.py")],
                   check=True, timeout=120)
    subprocess.run([sys.executable, str(root / "installer/verify_phoneme_build.py"), '--frozen'],
                   check=True, timeout=150)
    subprocess.run([sys.executable, str(root / "installer/verify_legacy_alias_build.py"), '--frozen'],
                   check=True, timeout=120)


def stamp(root: Path = PROJECT_ROOT) -> Path:
    """Call ONLY after executing the frozen EXE with --verify-layer2."""
    digests = _snapshot(root)
    _verify_gui(root)
    document = {
        "releaseMarker": RELEASE_MARKER,
        "builtUtc": datetime.now(timezone.utc).isoformat(),
        "testedFrozenExecutable": True,
        "filesSha256": digests,
    }
    destination = root / MANIFEST_PATH
    destination.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def verify(root: Path = PROJECT_ROOT) -> None:
    path = root / MANIFEST_PATH
    if not path.is_file():
        raise RuntimeError("No Layer 2 verified build stamp. Run BUILD_HEARLIUM_INSTALLER.bat first.")
    document = json.loads(path.read_text(encoding="utf-8"))
    if (document.get("releaseMarker") != RELEASE_MARKER
            or document.get("testedFrozenExecutable") is not True):
        raise RuntimeError("Old or unverified build stamp. Run the full installer builder.")
    if document.get("filesSha256") != _snapshot(root):
        raise RuntimeError("EXE or Layer 2 sources changed since the verified full build.")
    _verify_gui(root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("stamp", "verify"))
    args = parser.parse_args()
    try:
        if args.mode == "stamp":
            stamp()
            print("Stamped freshly tested Layer 2 executable and source.")
        else:
            verify()
            print("Layer 2 build integrity verified: installer uses the tested EXE.")
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: Layer 2 build verification failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
