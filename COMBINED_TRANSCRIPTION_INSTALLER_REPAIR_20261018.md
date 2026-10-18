> HISTORICAL NOTE: This document may describe an earlier PyAV/Faster-Whisper build. The current no-PyAV build excludes both packages and disables independent word ASR. See NO_PYAV_BUILD_NOTES.md.

# Combined Hearlium repair — October 18, 2026

Source: Hearlium_Transcription_Confidence_Learning_Fix_20261018, itself based on the user-supplied Hearlium_ParentPC_Installer_Dependencies_Fixed_20261018 ZIP.

## Included
- Separate Whisper word recognition from raw phonetic observation.
- Confidence and learning eligibility safeguards described in TRANSCRIPTION_CONFIDENCE_REPAIR_20261018.md.
- Pin PyAV to 16.1.0 after Faster-Whisper installation.
- Replace `inspect.signature(av.open)` validation, which can fail on PyAV built-in functions, with a real 16 kHz WAV decoding test using `av.open(..., metadata_errors="ignore")`.
- Preserve the existing Android, Bluetooth, Parent PC, and Windows installer project structure.

## Build
1. Extract to a NEW folder.
2. Run BUILD_HEARLIUM_INSTALLER.bat from that folder. It recreates .installer_venv and downloads prerequisites.
3. Check that `PortAudio, Faster-Whisper and PyAV 16.1.0 audio decoding: OK` appears.
4. Complete the Windows installer build and test a known counting recording.

Python syntax and ZIP integrity checked in this environment; full Windows build and Android APK were not executed here.
