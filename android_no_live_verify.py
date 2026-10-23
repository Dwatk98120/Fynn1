"""Refuse to build or distribute the legacy Live Recording Android mode.

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

    for marker in LEGACY:
        if marker in kotlin or marker in layout:
            raise ValueError(f"Legacy Live Recording source still present: {marker}")
    for marker in NORMAL:
        if marker not in layout:
            raise ValueError(f"Regular Android feature missing from layout: {marker}")
    for marker in ("startRecording()", "stopRecording()", "uploadForAnalysis()",
                   "SEND & ANALYZE ON PC"):
        if marker not in kotlin:
            raise ValueError(f"Regular recording/upload flow missing: {marker}")
    if not re.search(r"(?m)^\s*versionCode\s+7\s*$", gradle):
        raise ValueError("Expected fixed Android versionCode 7")
    if not re.search(r"(?m)^\s*versionName\s+['\"]3\.3\.1['\"]\s*$", gradle):
        raise ValueError("Expected fixed Android versionName 3.3.1")
    print("PASS: Android source has no legacy Live Recording mode; regular capture remains.")


def verify_apk(path: Path) -> None:
    if not path.is_file():
        raise ValueError(f"APK was not generated: {path}")
    with zipfile.ZipFile(path) as archive:
        dex_names = [name for name in archive.namelist() if
                     re.fullmatch(r"classes\d*\.dex", name)]
        if not dex_names:
            raise ValueError("No compiled Android DEX found in APK")
        dex_data = [archive.read(name) for name in dex_names]
    for marker in LEGACY:
        if any(marker.encode("ascii") in dex for dex in dex_data):
            raise ValueError(f"STALE APK: legacy Live Recording code found: {marker}")
    for marker in ("startRecording", "stopRecording", "recordButton", "stopButton"):
        if not any(marker.encode("ascii") in dex for dex in dex_data):
            raise ValueError(f"APK lacks expected regular recording feature: {marker}")
    print(f"PASS: compiled APK contains no legacy Live Recording symbols: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Hearlium Android no-live hotfix")
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
