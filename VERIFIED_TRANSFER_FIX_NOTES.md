# Android-to-Parent-PC Verified Transfer Fix

- Android Analyze Speech dialog uses a standard visible Send to PC button.
- Android posts WAV to `/v1/recording-receipt` first. The PC validates 16 kHz WAV and returns recording ID, byte count, and SHA-256 digest.
- Android verifies all three fields before showing PC receipt confirmation.
- Android then posts the WAV to `/v1/analyze-audio` and validates matching recording ID and observation in returned JSON.
- A receipt is transport verification only: it does not mean analysis has started, completed, or that audio is saved.
- Analysis failures and network errors are displayed with the recording ID.
- Android and Windows builds must be compiled and tested on target devices; no compiled APK or EXE included.
- Existing Bluetooth and caregiver review source retained.

## Build
Run `BUILD_HEARLIUM_INSTALLER.bat` on Windows for Parent PC. Build Android APK through the existing GitHub Android workflow. Both sides must be updated; older PC versions do not have the new receipt endpoint.
