Hearlium Parent PC - Analysis 500 Error Fix
===========================================
Fixes a confirmed NameError in POST /v1/analyze-audio: the server called
analyze_temporal_prosody(temp_path) without defining temp_path.
The server now passes the already uploaded WAV bytes directly to the
prosody analyzer, which accepts bytes or a filesystem path.

Verified: Python syntax compilation and standalone synthetic WAV prosody test.
NOT verified: Windows PyInstaller build, model download, or full microphone/API runtime.

Rebuild on Windows:
1. Extract this ZIP to a new folder (not under Program Files).
2. Run BUILD_HEARLIUM_INSTALLER.bat from that folder.
3. After successful build, install installer/output/HearliumSetup.exe.
4. Start Hearlium and retry recording/analysis.

If the API still returns HTTP 500, capture the server traceback: additional
model-loading or runtime failures may need separate fixes.
