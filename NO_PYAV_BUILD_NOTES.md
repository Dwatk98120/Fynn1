# Hearlium no-PyAV source build (2026-10-18)

Removed explicit PyAV and Faster-Whisper dependencies and collection, plus version-specific decoder checks. Faster-Whisper requires PyAV, so the independent word-ASR path returns `unavailable` in this edition. Phoneme CTC decoding, word-candidate ranking, speaker-learning safeguards, and the remaining 13-layer pipeline are retained. SoundFile handles WAV decoding tests.

To build: run `BUILD_HEARLIUM_INSTALLER.bat` in a clean Windows Python environment. The script attempts to uninstall old `av`, `faster-whisper`, and `ctranslate2` packages from its active build environment. Do not run against a shared environment. Test the resulting EXE with `--self-test`, and validate Bluetooth and speech processing on Windows before distribution.

This ZIP is source, not a precompiled installer. The build was not executed on Windows in this environment.
