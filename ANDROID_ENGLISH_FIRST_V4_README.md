# Hearlium Branch 2 Android English-first v4 display repair

This source-only update addresses the mismatch between the latest uploaded source and the phone screenshot.

## Key diagnostic
The uploaded v3 source already displayed `wordRecognition.text` and a Branch 2 marker, but the phone screenshot showed only `Heard:` followed by phonemes, and no marker. This is strong evidence of an old or different APK, not proof that the API failed.

## Changes
- Persistent on-start marker `Hearlium Android • English-first display v4 • Ready` in status; it should be visible before recording (auto-connect may temporarily replace status).
- Analysis display starts `ENGLISH-FIRST DISPLAY v4`, followed by independent `wordRecognition.text` and a separate raw phoneme section.
- Supports direct and nested analysis JSON shapes; does not substitute raw IPA for English words.
- Missing word results explicitly report recognizer status.
- Preserves recording, transfer verification, caregiver review, server code, and immutable evidence.

## Verify
1. Compile the APK via existing GitHub workflow. Download the artifact from that *specific* run.
2. Install that APK on the phone, then launch it. Confirm the `English-first display v4` marker before analyzing; if absent, check package installed / artifact and reinstall. Some auto-connect status messages can replace the ready marker, so the most reliable marker is at the top of the completed analysis result.
3. Record and analyze. Verify English appears under `POSSIBLE SPOKEN WORDS` and IPA under `OBSERVED SPEECH SOUNDS`.
4. If English unavailable, inspect the returned Raw JSON `wordRecognition` field and Parent PC logs. Do not interpret phoneme text as English.

Main baseline is not modified. APK and installer are not compiled in this environment.
