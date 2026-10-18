HEARLIUM BRANCH 2 - COMPLETE WINDOWS INSTALLER BUILD PROJECT
October 18, 2026

This is the complete Parent PC SOURCE and INSTALLER BUILD project, NOT a precompiled Windows Setup EXE.
Base: Hearlium_ParentPC_FasterWhisper_Hardened_ReleaseCandidate_20261018.zip
Integrated fix: server/main.py and server/android_recording_storage.py
Frozen packaging: explicit hidden imports for Android recording storage.

ON WINDOWS:
1. Keep your current working installation and recordings intact. Do not delete or replace them.
2. Extract this ZIP to a NEW SHORT path such as C:\here\Hearlium_Branch2_SaveFix.
3. Double-click BUILD_HEARLIUM_INSTALLER.bat. It requires Python 3.12, .NET 8 SDK, Inno Setup 6 and Internet access to download required build packages, offline Whisper model and official VC++ redistributable.
4. If all checks succeed, installer is installer\output\HearliumSetup.exe.
5. Before installing, back up %LOCALAPPDATA%\Hearlium\ParentPC and close the existing Hearlium app. Test on a non-production PC when possible.
6. After install, send a NEW Android test recording and verify response recordingStorage.saved=true and new android_*.wav + .json in %LOCALAPPDATA%\Hearlium\ParentPC\recordings.
7. Check the analysis_results folder and Recording History.

IMPORTANT:
- The prior source patch only persists successfully analyzed /v1/analyze-audio requests; /v1/recording-receipt is unchanged.
- A server-side error on saving now produces HTTP 500 instead of falsely claiming saved.
- WAV is written with exclusive creation and SHA256; existing files are not overwritten.
- The build's VC++ installer behavior is inherited from the base release candidate and currently runs the redistributable during installation; runtime conditional detection is not implemented in this bundle.
- This package has passed Python syntax and source comparison checks in a Linux environment, NOT a Windows installer compile or live Android upload test.
- Main branch and the protected working baseline were not modified.
