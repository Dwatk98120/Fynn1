# Hearlium Branch 2 — Phase 3 Evidence Integrity Hotfix (2026-10-22)

**Base:** Phase 3 Caregiver Review Usability + API Diagnostics Hotfix. **Main remains frozen.** Phase 2 baseline unchanged. No Android changes.

## Fixes

1. Selecting a recording first clears all analysis state, dashboard evidence and raw JSON before loading that recording's own saved analysis. Reanalyzing and starting a new recording invalidate prior analysis too.
2. Slow analysis responses cannot restore the previously selected recording or place old word boundaries in the current screen. Analysis is saved to its original audio file, but stale responses are ignored by the selected-recording UI.
3. Feedback submission binds the request to the file, speaker, word, notes and API URL selected at submission time. A concurrent selection change does not redirect local metadata or update the wrong recording's approval indicator. Duplicate in-flight submissions are blocked. Errors capture exception messages safely.
4. Individual word reviews are validated before writing anything. Approved clips are written to a unique staging directory and published in a unique final directory, **without overwriting previous approved clips**. The complete manifest is then atomically replaced. On any normal failure before manifest commit, only the new transaction is removed; old manifests and exports stay intact. On abrupt power loss, an unreferenced new clip directory may remain, but the old manifest still points to valid previous exports. Old clips are retained intentionally for auditing.
5. Installer version **0.4.3** checks the x64 Visual C++ v14 runtime's installed registry version against the official bundled installer version. Compatible/newer runtimes are not touched. Missing/older runtimes display a checked installation task that users can deselect. The installer checks the subprocess exit code, reports failures and requests a reboot for exit code 3010/1641. Setup will not auto-launch Hearlium if the runtime is declined or a restart is pending.

## Build (Windows)

1. Extract the full ZIP to a **new, short folder**, such as `C:\Hearlium3`.
2. Run `BUILD_HEARLIUM_INSTALLER.bat`. It downloads the official Microsoft VC++ redistributable during build, tests Python code and builds Windows components, then compiles the Inno Setup installer using the existing short-path SUBST workaround.
3. The compiled output, after a successful build, is `installer\output\HearliumSetup.exe`.
4. Install on a test PC and verify saved reviews survive restart. Do **not** approve new personalized-learning examples until the API reliability and evidence tests pass in normal use.

## Tests and limitations

- Run: `python -m pytest -q server/tests`.
- Targeted regression tests cover stale-recording selection, late analysis, cross-recording feedback, partial clip-write errors, failed manifest publication, duplicate approved clips, and installer source safeguards.
- This ZIP is **complete source**, not a Windows `.exe`. PyInstaller, Inno Setup and official VC++ prerequisite packaging require Windows and were **not executed here**.
- No server/API drop-out root cause was changed; diagnostic logging is preserved.
- No student recordings from the user's machine were used, accessed, changed, or embedded in this package.
