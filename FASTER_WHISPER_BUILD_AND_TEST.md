# Faster-Whisper integration and validation

This build restores optional Faster-Whisper CPU/int8 word hypotheses. PyAV is **required**, not removed. Word hypotheses are never approved learning feedback. The phoneme engine remains primary.

## Windows build
Run `BUILD_HEARLIUM_INSTALLER.bat` in a NEW extracted directory, not the protected `C:\HearliumPack`. The script requires Python 3.12 x64, .NET 8 SDK, Inno Setup 6, internet for dependencies and VC++ redistributable. It installs pinned native wheels and runs `pip check`, PyAV decoding, and a frozen `--self-test` before invoking Inno Setup.

## Offline models
By default `HEARLIUM_ASR_LOCAL_ONLY=1`; the optional ASR reports unavailable until a model is cached or `HEARLIUM_ASR_MODEL` points to a locally available compatible model directory. To allow first-time Hugging Face download set `HEARLIUM_ASR_LOCAL_ONLY=0` on a trusted connected PC. Do not treat a missing model as a failed primary speech engine. Model weights are **not bundled** in this source ZIP.

## Remaining release gates
On Windows: verify pinned wheels are available; PyInstaller build; `dist\HearliumParentPC\HearliumParentPC.exe --self-test`; actual model transcription; clean Inno installation; Bluetooth pairing, Android upload, speech analysis, offline restart, uninstall and reinstall with learning data preserved. A Linux source check does not verify Windows native DLL loading.

## Compatibility note
The pins are a candidate tested set, **not proven compatible on this Windows machine**. If wheel resolution fails, stop and inspect the build log; do not silently remove PyAV or downgrade unrelated libraries.
