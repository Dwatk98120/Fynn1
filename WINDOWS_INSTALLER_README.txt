HEARLIUM PARENT PC — UPDATED WINDOWS INSTALLER BUILDER
======================================================
This source package uses the latest Temporal / Prosody Parent PC backend.

Build on a Windows x64 PC with:
  - Python 3.12 (py -3.12)
  - Inno Setup 6
  - internet access for Python dependencies and Microsoft VC++ runtime
  - optional .NET 8 SDK for Bluetooth helper

STEPS
1. Extract the ZIP into a NEW normal Windows folder.
2. Double-click BUILD_HEARLIUM_INSTALLER.bat.
3. Allow the downloads and compilation to finish.
4. Find the completed installer at installer\output\HearliumSetup.exe.
5. Run that setup EXE on the Parent PC.

The builder will:
 - install dependencies with the Windows quoting fix
 - build a single frozen HearliumParentPC.exe with --server/--record/--pair modes
 - bundle the Bluetooth helper when .NET 8 SDK is installed
 - download and bundle the Microsoft Visual C++ x64 runtime (required by Torch)
 - offer to install/repair that runtime on the build computer before Python checks
 - run a frozen import self-test before packaging
 - compile the Windows installer with Inno Setup

The installed program keeps learning data and recordings under:
  %LOCALAPPDATA%\Hearlium\ParentPC\
This location survives application updates/uninstalls by default.

Important:
 - The phoneme AI model may download on first analysis, requiring internet once.
 - Speech audio and analysis run on the local Parent PC / LAN after setup.
 - The Android APK is NOT installed by this Windows installer.
 - This ZIP is a builder, not a precompiled Windows installer.
 - Windows build and actual microphone/Bluetooth tests are still required.
 - The Microsoft Visual C++ runtime installer may request a reboot.
