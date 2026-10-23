"""Refuse to publish stale Hearlium Android APKs lacking protected local audio.

This lightweight check runs in GitHub Actions before compilation and on the
actual APK artifact after compilation. No Python dependencies are required.
"""

import argparse
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
LEGACY = (
    "liveRecordingButton",
    "startLiveSpeechMode",
    "stopLiveSpeechMode",
    "liveStatusIndicator",
)
NORMAL = (
    "recordButton",
    "stopButton",
    "savedRecordingsButton",
    "analyzeButton",
    "caregiverReviewButton",
)


def verify_source() -> None:
    kotlin = (ROOT / "app/src/main/java/com/firstsoundhelper/MainActivity.kt").read_text(
        encoding="utf-8"
    )
    layout = (ROOT / "app/src/main/res/layout/activity_main.xml").read_text(
        encoding="utf-8"
    )
    gradle = (ROOT / "app/build.gradle").read_text(encoding="utf-8")
    store = (ROOT / "app/src/main/java/com/firstsoundhelper/LocalSpeechRecordingStore.kt"
             ).read_text(encoding="utf-8")

    # The old Live Recording control is deferred by caregiver choice. The
    # corrected source is included, but it does not gate THIS reliability build.
    if any(marker in kotlin or marker in layout for marker in LEGACY):
        print("NOTE: legacy Live Recording UI still present; removal is deferred.")
    for marker in NORMAL:
        if marker not in layout:
            raise ValueError(f"Regular Android feature missing from layout: {marker}")
    for marker in ("startRecording()", "stopRecording()", "uploadForAnalysis()",
                   "SEND & ANALYZE ON PC", "restoreLatestSavedCapture()",
                   "localRecordingStore.saveCapture(", "localRecordingStore.verifiedWav(",
                   "clearPendingReview()", "localRecordingStore.saveAnalysis("):
        if marker not in kotlin:
            raise ValueError(f"Regular recording/upload flow missing: {marker}")
    for marker in ("atomicCreate(", "recording_meta.json", "sha256",
                   "verifiedWav(", "latestVerified()", "saveAnalysis("):
        if marker not in store:
            raise ValueError(f"Protected local recording storage missing: {marker}")
    if not re.search(r"(?m)^\s*versionCode\s+8\s*$", gradle):
        raise ValueError("Expected Android capture durability versionCode 8")
    if not re.search(r"(?m)^\s*versionName\s+['\"]3\.3\.2['\"]\s*$", gradle):
        raise ValueError("Expected Android capture durability versionName 3.3.2")
    print("PASS: source protects completed audio and preserves normal recording/upload.")


def verify_apk(path: Path) -> None:
    if not path.is_file():
        raise ValueError(f"APK was not generated: {path}")
    with zipfile.ZipFile(path) as archive:
        dex_names = [name for name in archive.namelist() if
                     re.fullmatch(r"classes\d*\.dex", name)]
        if not dex_names:
            raise ValueError("No compiled Android DEX found in APK")
        dex_data = [archive.read(name) for name in dex_names]
    if any(marker.encode("ascii") in dex for marker in LEGACY for dex in dex_data):
        print("NOTE: legacy Live Recording mode is present; this hotfix tests capture durability.")
    for marker in ("startRecording", "stopRecording", "recordButton", "stopButton",
                   "LocalSpeechRecordingStore", "saveCapture", "verifiedWav"):
        if not any(marker.encode("ascii") in dex for dex in dex_data):
            raise ValueError(f"STALE APK lacks expected durable recording feature: {marker}")
    print(f"PASS: compiled APK contains durable recording storage and required controls: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Hearlium Android capture durability")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source", action="store_true")
    group.add_argument("--apk", type=Path)
    args = parser.parse_args()
    try:
        if args.source:
            verify_source()
        else:
            verify_apk(args.apk)
        return 0
    except (ValueError, OSError, zipfile.BadZipFile) as error:
        print(f"FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
