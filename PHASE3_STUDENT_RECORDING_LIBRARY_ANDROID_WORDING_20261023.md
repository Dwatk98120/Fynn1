# Hearlium Branch 2 — Phase 3 Student Recording Library + Android Phoneme Wording

Date: 2026-10-23. Built from Phase 3 Recording & Review Audit Safety hotfix.
Main stays frozen; Phase 2 remains a protected baseline. No cloud endpoints added.

## Parent PC — Recording History

* **Student** dropdown filters by exact stored `speakerId`, not by guessed name.
* Friendly **student display names** can be added to a specific speaker ID after a confirmation prompt. This mapping lives in `%LOCALAPPDATA%\Hearlium\ParentPC\student_profiles.json`, with attempted and committed changes in `student_profile_audit.jsonl`.
* Changes to display names **do not change WAV files, original metadata, observation IDs, learning records, or the server**.
* Search accepts student display name, speaker ID, filename, and reviewed word (case-insensitive).
* Date range accepts `YYYY-MM-DD`, with explicit validation on bad/reversed dates.
* Sort by newest first, oldest first, student A–Z, student Z–A, or recording name A–Z.
* The recording count reflects active filters. The Unassigned view includes missing IDs and legacy/shared IDs such as `anonymous` and `student-1`.
* Existing local Parent PC recordings and received Android recordings appear in the same list if their WAV files are in the configured recordings folder.
* Recording navigation protections and immutable-evidence rules from the previous Phase 3 hotfix remain in place.

**Important identity limitation:** The current Android application uses a persistent speaker ID per app installation, not a verified per-student selection. If several students record on the same phone, that ID might be shared. The new name-mapping dialog warns caregivers to label an ID only if *all* recordings with that ID belong to the same student. Unassigned/legacy shared IDs cannot be named through this control. A true multi-student selector on Android is separate future development, not part of this ZIP.

## Android — Phoneme result explanation

Replaces the misleading "These sounds are not English words" explanation with:

> These symbols show how Hearlium thinks the speech sounded, not ordinary English word spellings. Compare them with the suggested words above and listen to the original recording. Some sounds may be uncertain, and only a caregiver can confirm the intended words.

Candidate English words and phoneme observations stay separate. No speech engine, server analysis, feedback, or training logic changed.

## Build / Installation

### Windows Parent PC

1. Extract the whole ZIP to a **short new path**, e.g. `C:\Hearlium3` (avoid building inside long backup paths).
2. Run `BUILD_HEARLIUM_INSTALLER.bat` on the Windows Parent PC.
3. Install `installer\output\HearliumSetup.exe` after a successful build.
4. Open **Direct Recording → Recording History** and verify the new filters.
5. Keep protected previous source and installer backups.

### Android APK via GitHub (no Android Studio required)

1. Upload/commit this ZIP's Android project files on **Branch 2** only. Do not merge Main.
2. On GitHub **Actions**, use the manual **Build Android APK** workflow and choose Branch 2. The workflow downloads an official Gradle 8.9 distribution and generates its wrapper during CI.
3. Download the Android debug APK artifact from the successful workflow run.
4. Verify the text inside **Analyze Speech** / response trace on the newly installed Android app.

The ZIP contains source code, **not** a Windows installer or Android APK. Neither platform-native build was executed in this environment.

## Verification

* 98 Python regression tests passed (plus eight unittest subtests).
* GUI smoke test under Xvfb passed for full listing, search, student filtering, date filtering and unassigned view.
* Python source compiled and ZIP checked for integrity.
* Windows Inno and real GitHub Android APK builds must still be verified.
* Existing Phase 3 random API connection dropout is **not** claimed resolved.
