# Hearlium Android ONLY — No Live Recording Hotfix

Date: 2026-10-23
Target: GitHub Branch 2 (`hearlium-parent-pc-integration`). **Do not change Main.**

## What this download contains

- Full Android app source and required Gradle/GitHub build files; **no Windows
  Parent PC application or installer**.
- The legacy Live Recording button/mode is removed from Android.
- The ordinary **Record Speech**, **Stop**, **Saved Recordings**, **Analyze**,
  **Caregiver Review**, and **Send & Analyze on PC** flows are retained.
- Android version is **3.3.1** (`versionCode 7`) to distinguish this hotfix
  from stale `3.3/code 6` APKs.
- GitHub Actions checks the source *and the compiled APK* for the old live
  recording controls/methods. If they are found, no APK will be uploaded.
- Local Windows Parent PC remains the only analysis/storage/API server.

## Build with GitHub Actions

1. Unzip this archive.
2. On GitHub, switch to **hearlium-parent-pc-integration** (Branch 2).
3. Copy the enclosed project files and folders into the **repository root on
   Branch 2**, replacing matching Android/build workflow files.
   **Do not commit the ZIP as a single unextracted file**; GitHub will not build
   updated source from a ZIP sitting in the repository.
   Keep the existing Parent PC/server files in the repository unchanged.
4. Commit to Branch 2. The workflow **Hearlium Android APK - No Live Recording
   v3.3.1** should start automatically. You can also use **Run workflow** on
   that branch.
5. When the action succeeds, download its artifact
   **Hearlium-Android-NoLive-v3.3.1-code7**.
6. Install `app-debug.apk` from that artifact. It is a debug APK for testing.

If the compiled APK contains `startLiveSpeechMode`, `stopLiveSpeechMode`,
`liveRecordingButton` or `liveStatusIndicator`, the workflow now stops before
publishing a stale build.

## Scope and testing

This ZIP contains source, not a prebuilt APK. Python source checks and the
stale-APK detector were tested locally. Android compilation and testing on a
device still occur through GitHub Actions and your phone.

Protected Main and the known-good Windows installer baseline remain unchanged.
