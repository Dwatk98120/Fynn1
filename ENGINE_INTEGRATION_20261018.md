> HISTORICAL NOTE: This document may describe an earlier PyAV/Faster-Whisper build. The current no-PyAV build excludes both packages and disables independent word ASR. See NO_PYAV_BUILD_NOTES.md.

# Hearlium Parent PC — newest engine integration review (2026-10-18)

## Existing engine confirmed in source
- 13-layer pipeline including human feedback, speaker adaptation, pattern and strategy learning, and self-evaluation.
- Immutable observation snapshots, review-only interpretation, CTC tokenizer decoding, adaptive segment boundaries, number review, and isolated reference comparisons.
- Candidate scores are heuristic ranking values, not validated speech-recognition probabilities.
- Human confirmation is required before learning; this package does not enable autonomous training.

## Integration changes in this ZIP
1. Frozen launcher self-test checks real PyAV WAV decoding instead of rejecting all versions other than 16.1.0.
2. PyInstaller spec explicitly includes the newer server modules that may be dynamically loaded.
3. Preserved Android source, installer script, Bluetooth code, and existing recording paths without unrelated edits.

## Validation and limitations
Run `python -m unittest discover -s server/tests -v` from the extracted root.
This is an updated SOURCE ZIP, not a compiled Windows installer or Android APK. Rebuild on Windows and validate real speech recordings and Bluetooth connectivity. The exact installed model/tokenizer pair and Windows dependencies cannot be validated here.

## Windows build
Keep your existing working `C:\HearliumPack` and backups intact. Extract this source to a NEW folder and run the included BUILD_HEARLIUM_INSTALLER.bat according to README_BUILD_THIS_INSTALLER.txt. Do not overwrite the known-good build until installation testing succeeds.
