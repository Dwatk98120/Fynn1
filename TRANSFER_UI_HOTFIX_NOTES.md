# Android Send & Analyze UI hotfix

- Replaced the cramped Android AlertDialog with a full-width, scrollable popup and a clearly visible **SEND & ANALYZE ON PC** action.
- Added a **Test PC Connection** button to the same popup.
- Changed misleading **Parent PC saved** text to **address saved (not yet verified)**.
- Added a clear outdated-server message when /v1/recording-receipt is missing (HTTP 404/405).
- The phone verifies PC receipt by recording ID, SHA-256 and byte length, then submits to /v1/analyze-audio and verifies the returned recording ID.
- Receipt endpoint verifies transport but does **not** permanently store the file. The subsequent analysis request sends the audio again. A successful receipt does not prove the PC has saved the recording; the UI deliberately avoids that claim.

## Required deployment
Build a **new Android APK** from this source using the GitHub build-apk workflow and install that APK on the phone. Building the Windows installer alone will not update the Android UI. Install/run the matching Parent PC build too. On the phone, open Parent PC Connection > Test Connection before recording.

## Verification limits
Source code and ZIP packaging checked in this environment; a real Android APK build and live phone-to-PC test are still required.
