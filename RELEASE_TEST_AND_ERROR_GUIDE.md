# Hearlium release-candidate test plan (Windows x64)

**Not a certified Windows build.** Source checks here cannot substitute for Windows DLL/model/runtime checks.

## Preflight
1. Build in a NEW folder, keep `C:\HearliumPack` untouched.
2. Python 3.12 x64, .NET 8 SDK, Inno Setup 6, disk space (allow 8+ GB), internet for model download.
3. Run `BUILD_HEARLIUM_INSTALLER.bat` and save the complete terminal output.
4. Confirm `installer\resolved-dependencies.txt` and model assets; do not commit or share private student recordings.

## Errors to watch for
- `No matching distribution found for av`: Python/Windows wheel compatibility; ensure Python 3.12 x64.
- `DLL load failed`, `c10.dll`, `ctranslate2`: missing Visual C++ runtime or mismatched binaries.
- `pip check` conflict: stop build; don't force-install conflicting versions.
- `Offline model assets missing`: network/Hugging Face failure or incomplete download; retry, don't bypass.
- `collect_all failed`: PyInstaller missing dependency; build now stops instead of silently shipping incomplete output.
- Frozen `--self-test` failure: DLL/import issues; don't run Inno Setup until fixed.
- `ISCC` error: verify Inno Setup 6 installed; keep existing working installer.
- Windows firewall: check netsh exit status and actual rule after installation; don't overwrite unrelated rules.
- Startup: verify correct Windows user/account and sign-in behavior; common startup affects all users.
- Audio upload HTTP 503: verify server logs, model startup and firewall; do not assume installer failure.
- Privacy: confirm no unexpected cloud audio/model requests at runtime; model is bundled for offline use.

## Second-stage release acceptance (must be performed on Windows)
1. Clean install to a separate test PC/VM; verify GUI/server/Bluetooth start.
2. Run installed EXE `--self-test`; transcribe a known spoken WAV with the offline model.
3. Transfer Android recording over Wi-Fi, then Bluetooth; check response and session storage.
4. Test absent microphone, no network, low memory, repeated launch and reboot.
5. Test uninstall/reinstall and that recordings and learned data survive or are backed up.
6. Review errors and rerun the entire sequence after fixes.

Model inference and the complete installer cannot be verified in this Linux environment.
