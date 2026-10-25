# Hearlium Branch 2 — Complete Runtime Dependency Preflight (October 25, 2026)

## Windows evidence

On the earlier Windows installer build, **239 tests passed, 3 skipped** and
`pip check` found no broken declared dependencies. The subsequent real
audio smoke test failed because `soundfile` was missing. A separate
read-only check of the exact `.installer_venv` interpreter showed these
unavailable imports: `soundfile`, `sounddevice`, `silero_vad`. Other tested
audio packages, `av`, `ctranslate2` and `faster_whisper`, were present.

`pip check` cannot establish that all application imports exist. The earlier
build had also required automatic recovery of `requests` and `nltk`.

## Fix

1. The Windows installer builder runs a new explicit interpreter audit at
   `installer/ensure_build_dependencies.py --repair` before any regression
   tests or model packaging.
2. It checks the import/module **and pinned distribution version** for all
   direct runtime, speech/audio and build Python packages, including
   `soundfile==0.13.1`, `sounddevice==0.5.2` and `silero-vad==6.2.3`.
3. A missing or incompatible installed package is repaired using a known,
   pinned pip command **only inside the disposable `.installer_venv`**;
   it never changes global Python or a compatible original audio file.
4. Repairs must result in an independently detectable installed module at
   the pinned version. Any failure stops the build. Specialized installation
   flags are retained for older `distance` and `g2p-en` packages.
5. The builder still performs `pip check`, the full pytest suite,
   PyAV/Faster-Whisper native smoke tests, actual offline Silero model
   inference, PyInstaller and Inno Setup compilation.
6. The Windows runtime always uses its isolated Python interpreter; the
   Android app, target recording bytes, 13-layer analysis engines, model
   versions, caregiver approvals and protected Main branch are unchanged.

## Build and verification

This is a **complete source ZIP** for the working Branch 2, not a compiled
Windows installer. On a Windows machine, extract into a new folder and run
`BUILD_HEARLIUM_INSTALLER.bat`. Allow the dependency check to finish before
reading the test results. Check for:

- `All required build dependencies are present at pinned versions.`
- `No broken requirements found.`
- All regression tests passing, and separately documented skip reasons.
- `PyAV WAV decode and Faster-Whisper native imports: PASS`.
- `Silero VAD bundled model and offline inference: PASS`.
- A newly frozen and self-tested Parent PC EXE, then an Inno Setup installer.

The existing **239 passed / 3 skipped** result belongs to the earlier build,
not this modified one. An installed runtime or offline Silero model should
not be treated as verified until the new Windows smoke tests succeed.
