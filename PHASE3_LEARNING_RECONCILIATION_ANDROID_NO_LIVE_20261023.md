# Hearlium — Branch 2 Phase 3 Learning Reconciliation + Android No-Live Hotfix

**Date:** 2026-10-23  
**Complete source base:** `Hearlium_Branch2_Phase3_Feedback_Rollback_Reliability_Hotfix_20261023.zip`  
**Branch:** `hearlium-parent-pc-integration` only. **Main and the Phase 2 working baseline remain untouched.**  
**Build output:** This ZIP contains source, tests and the Windows build scripts; it does **not** contain a precompiled Windows EXE or Android APK.

## Included fixes

1. **Previously approved word corrected:** Before sending a new caregiver correction or replacement approval, Parent PC durably retains the previous server example ID, marks the rollback pending, and requests revocation. The replacement is sent only after the local server confirms that exact old example was revoked. If rollback cannot be confirmed, the replacement is NOT submitted; the original approval reference remains available and the recording stays `ACTION_REQUIRED`. Server references are retained in `learningApprovalReferences`, including revocation status, rather than overwritten by `learningFeedback`.
2. **HTTP 400 after Unsure/Reject:** Definite 4xx feedback rejection clears the matching request ID from `feedbackPending` or `supersededFeedbackPending` irrespective of the latest caregiver review revision, without altering unrelated requests or rollback failures.
3. **Manual Learning History rollback:** Once the local learning server confirms the selected example ID as revoked, Parent PC matches the speaker ID, recording ID, observation ID and example ID to recording metadata and reconciles that approval's pending/failure state. Other recordings, other pending approvals and uncertain examples remain blocked. Missing/ambiguous identity is reported rather than guessed; segment approvals cannot be matched solely by a shared observation ID.
4. **Android Live Recording removed:** Removes the main-screen Live Recording button, its indicator, its recognizer/live-audio streaming thread and live-session UI implementation. **Ordinary Record speech, Stop, saved recordings, sending to Parent PC, analysis, word bank and caregiver review remain.** The previously verified phoneme explanation is retained.
5. **Android version:** `app/build.gradle` is now versionCode **6**, versionName **3.3** to distinguish this APK from the preceding 3.2 source.

## Verification completed

- `PYTHONPATH=.:server:parent_pc_local pytest -q server/tests`: **143 passed, 8 subtests passed**.
- `python -m compileall -q parent_pc_local server`: **passed**.
- `xvfb-run -a python phase3_consistency_ui_smoke.py`: **passed** (Android export review, history search and analysis invalidation).
- Android layout XML syntax and no-live static checks: **passed**.
- Complete source ZIP tested for CRC/file integrity: **passed**.

**Not yet verified here:** Windows Inno Setup installer compilation, Android Gradle/APK compilation (the build environment has no Android SDK), real Android device/UI testing, network failures on a real Windows Parent PC, and long-running learning safety. Use disposable recording data when testing. No model code or user recordings were changed.

## Build/install on Windows

1. Keep a backup of the last confirmed working installer and user data. Extract this new full source ZIP into a **separate** folder (e.g. `C:\Hearlium3_LearningReconcile`).
2. Run `BUILD_HEARLIUM_INSTALLER.bat` in the extracted source to build the Windows Inno Setup installer, then install its output for testing. Existing user data in `%LOCALAPPDATA%\Hearlium\ParentPC` is *not* contained in this ZIP. Make a backup before changing installations.
3. For Android, commit the updated `app/src/main/java/com/firstsoundhelper/MainActivity.kt`, `app/src/main/res/layout/activity_main.xml` and `app/build.gradle` to **Branch 2** and run the **Build Android APK** GitHub Action on Branch 2. Installing the Windows program does not update the APK. If APK signing changed, back up Android private recordings before uninstalling anything.
4. Confirm the main Android screen has **Record speech**, **Stop**, **Analyze speech**, **Saved Recordings**, and **no Live Recording** button. Confirm a fresh recording can be analyzed and sent and the phoneme explanation displays.
5. With **disposable** test approvals only, try: approve then correct; approval then reject; Unsure while an approval is in flight followed by definite 400; rollback through Learning History; failed rollback; retry nonlearning correction after an interrupted request. Inspect the matching server example and metadata after each.
6. **Do not bypass an existing `ACTION_REQUIRED` review warning.** A request with an unknown server outcome requires manual learning-ledger reconciliation.

## Files changed versus the previous complete hotfix

- `parent_pc_local/direct_recording.py`: approval reference history, safe revoke-before-replace, HTTP 4xx cleanup, local manual reconciliation.
- `parent_pc_local/phase3_learning_gui.py`: server-confirmed manual rollback now reconciles matching recording status and reports the outcome.
- `server/tests/test_phase3_feedback_rollback_reliability_hotfix.py`: additional regression tests including races, manual rollback isolation and Android no-live source checks.
- `app/src/main/java/com/firstsoundhelper/MainActivity.kt`: Android Live Recording implementation removed; normal recording and verified phoneme wording retained.
- `app/src/main/res/layout/activity_main.xml`: Live Recording button and indicator removed.
- `app/build.gradle`: version 3.3 (code 6).

The local Python traceback/server logs remain in place. No Render/cloud service is introduced. Main remains frozen.
