# GitHub repository setup — Hearlium 0.4.19

## What this folder is
A GitHub-ready **source snapshot**, not an installed application and not proof that Windows or Android builds succeeded on your device. This package has not been pushed to GitHub.

## Safe integration into existing repository
1. Back up your current GitHub branch and note its commit ID.
2. In GitHub, select branch `hearlium-parent-pc-integration` (not Main).
3. Compare the snapshot against the current branch. **Do not upload over newer changes without reviewing differences.**
4. Commit reviewed source and docs only. Exclude recordings, credentials, `.installer_venv`, generated builds, and logs.
5. Use Actions > `Verify Hearlium Parent PC Source` for source checks.
6. Use the existing `Build Android APK` workflow for an Android APK. It bootstraps Gradle 8.9 and regenerates the wrapper JAR; `./gradlew` will not work directly from a clean checkout until the wrapper is generated.
7. To create a Windows installer, use Windows with Python 3.12, Inno Setup and the build prerequisites, then run `BUILD_HEARLIUM_INSTALLER.bat`. The expected source-release path is `installer/output/HearliumSetup-0.4.19.exe`; the executable is **not** included in this source ZIP.
8. Test the installed app, reanalysis, Android upload, and original WAV count/hashes before approving a release.

## Validation in this packaging environment
- `python -m compileall -q server parent_pc_local shared` — PASS.
- `python -m pytest -q server/tests` — **462 passed, 4 skipped, 45 subtests passed**.
- Android Gradle build — NOT RUN (requires Android SDK/Gradle setup).
- Windows Inno Setup installer build — NOT RUN (requires Windows).
- Real-device acceptance — NOT RUN.

The original 0.4.19 README reported 463 passed, 3 skipped from a different test environment; this package preserves that README and distinguishes its claims from this run.
