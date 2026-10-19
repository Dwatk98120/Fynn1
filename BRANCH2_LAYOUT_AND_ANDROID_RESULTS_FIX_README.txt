HEARLIUM BRANCH 2 — WINDOW LAYOUT AND ANDROID RESULTS PATCH

Changes:
- Parent PC Record & Analyze tab now has a vertical scrollbar to reach caregiver-review and bottom controls on smaller screens / high DPI.
- Android displays independent Faster-Whisper word suggestions first when available, with explicit uncertainty; raw phoneme text is labeled technical and unverified.
- Android no longer leads the result display with a long recording UUID; IDs remain in Record Details.
- Inno Setup firewall uninstall entry repaired (missing semicolon before RunOnceId) to prevent the known line-45 build failure.
- Existing server evidence and recording-persistence code is unchanged.

Build Windows: extract into a NEW folder, then run BUILD_HEARLIUM_INSTALLER.bat.
Build Android: push updated app/src/main/java/com/firstsoundhelper/MainActivity.kt to Branch 2 and use existing GitHub Actions APK workflow.
IMPORTANT: The Windows installer does not install the Android APK. Both need to be rebuilt for the two fixes.

Validation: Python syntax checked. No Windows UI or Android runtime build was executed here. Test at 100/125/150% scaling and verify Faster-Whisper wordRecognition.status from a fresh recording.
Do not delete or overwrite original recordings; leave Main and the working baseline untouched.
