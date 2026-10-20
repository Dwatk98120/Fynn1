# Android Response Trace v5 (Branch 2 only)

- Persistent on-screen build label visible without recording.
- `versionCode` 5 to distinguish this APK from previous installations.
- Recursive lookup for `wordRecognition.text` across common JSON wrappers.
- Raw phoneme observations displayed separately and never substituted for English.
- Response key/status diagnostics visible after analysis, without exposing full audio or personal context.
- No changes to server, recordings, caregiver learning permissions, or Main.

## Diagnostic decision
If the persistent v5 label is absent, the running app is not this source build. If present, run Analyze speech > Send & Analyze and inspect the diagnostics line. If `wordRecognition=missing`, capture the response JSON for the same recording ID.

## Build validation
Source-level static checks and ZIP integrity only. APK compilation and on-device verification must be done via GitHub Actions and device.
