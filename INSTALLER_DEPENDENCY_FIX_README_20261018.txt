> HISTORICAL NOTE: This document may describe an earlier PyAV/Faster-Whisper build. The current no-PyAV build excludes both packages and disables independent word ASR. See NO_PYAV_BUILD_NOTES.md.

HEARLIUM PARENT PC - WINDOWS INSTALLER DEPENDENCY REPAIR
=======================================================
Source: Hearlium_Enhanced_Decipher_Dual_Engine_20261017(1).zip

Changes:
- Installer build now installs faster-whisper and pins PyAV av==16.1.0.
- The builder runs pip check and import/API checks for PortAudio, Faster-Whisper, and PyAV.
- PyInstaller explicitly collects faster_whisper, ctranslate2 and av.
- Frozen executable --self-test now checks Faster-Whisper import and PyAV version/API.
- Speech ASR requirements file also pins av==16.1.0.
- Missing Inno Setup now reports incomplete installer build (nonzero exit code).

Build on Windows:
1. Extract this ZIP to a new folder, for example C:\HearliumBuild\herelium.
2. Install Python 3.12 x64, .NET 8 SDK x64 and Inno Setup 6.
3. Double-click BUILD_HEARLIUM_INSTALLER.bat (or run from CMD).
4. On success, installer is at installer\output\HearliumSetup.exe.

NOTE: A working Python environment does NOT prove the frozen installer works.
The batch script must build and self-test the frozen executable on Windows.
Model download on first transcription still requires network access unless
models are separately prepackaged. No model weights are included in this ZIP.

This source ZIP has been statically checked, but NOT built on Windows here.
The Android and other source files are preserved from the supplied archive.
