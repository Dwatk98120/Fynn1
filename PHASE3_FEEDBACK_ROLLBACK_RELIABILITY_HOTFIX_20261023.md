# Hearlium — Branch 2 Phase 3 Feedback & Rollback Reliability Hotfix

**Date:** 2026-10-23  
**Base:** `Hearlium_Branch2_Phase3_Caregiver_Decision_Approval_Integrity_Hotfix_20261023.zip`  
**Android addition:** Includes the already-verified `Hearlium_Android_Phoneme_Explanation_Install_Fix_20261023.zip` source (`MainActivity.kt` and `app/build.gradle`, version 3.2).  
**Scope:** Parent PC caregiver feedback safety, plus preservation of the confirmed Android display wording.  
**Main:** frozen; **Phase 2 working baseline:** untouched. No repository pushes performed.

## Resolved issues (three October 23 findings)

1. **Critical — New approval while a prior revocation is `pending`.** Review submission now checks active rollback states (`pending`, `awaiting_api_resolution`, `ACTION_REQUIRED`) in addition to pending feedback markers, both *before* and *inside* the metadata transaction that reserves a new decision. Every revocation started for an already accepted approval has its own durable `learningRevocationId`. Newer caregiver decisions must not erase the rollback gate; the rollback worker records failure even after `reviewRevision` advances.

2. **Medium — Reanalysis strands `feedbackPending` after confirmed revocation.** Every approval request now carries a unique `requestId`; the server outcome reconciles exactly that request, regardless of later observation IDs or review revisions. A **confirmed** revocation clears only the matching old `feedbackPending` / `supersededFeedbackPending` marker and updates its linked status. A failed revocation sets `ACTION_REQUIRED`, persists its audit and continues blocking learning approvals. Unrelated pending requests or failures are *not* removed by a successful rollback. Starting reanalysis while this window has an actively running feedback request is blocked, closing an additional race.

3. **Medium — Failed correction-only save incorrectly blocks retry.** If a `Confirm & Save` / `Save Correction Only` request **did not request learning approval**, a connection failure removes only the matching local pending reservation. It does not falsely create an unresolved learning-approval warning; the caregiver may inspect history and retry. This does not clear or override any *separate* unresolved learning approval or revocation. An HTTP request can still have been accepted before its response was lost; caregiver review history should be checked to avoid duplicate correction records.

## Safety behavior and limits

- Original WAV files, acoustic observations, prior reviews, student assignments and analysis exports are not rewritten by these repairs.
- Approved learning remains restricted to the local Windows Parent PC. Android talks to it locally; no cloud services are introduced.
- Accepted but superseded learning approvals are recorded in `%LOCALAPPDATA%\Hearlium\ParentPC\feedback_observation_audit\` before attempted revocation via the local-only learning endpoint.
- **A lost approval response is still ambiguous.** Until the server state can be independently verified, `ACTION_REQUIRED` must remain and personalized learning should not be used for that recording. Never delete the audit to bypass the lock.
- A successful rollback can close an `ACTION_REQUIRED` marker **only if the request ID identifies that same approval**; unrelated failures remain blocked.
- The bug fixes do not retroactively reconcile old uncertain approvals. Review them in **Phase 3 Learning History**.

## Source changes

- `parent_pc_local/direct_recording.py`: request IDs, rollback IDs and safe metadata reconciliation; learning-pending gate; correction retry handling; reanalysis guard.
- `server/tests/test_phase3_feedback_rollback_reliability_hotfix.py`: race and recovery regression tests.
- `app/src/main/java/com/firstsoundhelper/MainActivity.kt` and `app/build.gradle`: carries forward the Android phoneme-explanation fix you visually verified, version 3.2.

## Verification in build environment

- `PYTHONPATH=.:server:parent_pc_local pytest -q server/tests`: **136 passed, 8 subtests passed**.
- `xvfb-run -a python phase3_consistency_ui_smoke.py`: **PASS** (recording review, Android saved analysis and history search).
- `python -m compileall -q parent_pc_local server`: **PASS**.
- Full ZIP CRC/integrity check: **PASS**.

Automated simulations do **not** replace real Windows testing with disposable recordings. No Windows Inno Setup installer or APK is precompiled in this source archive.

## Build and test on Windows

1. Keep your current known-good installer and user-data backups. Unzip this **complete source** into a new folder such as `C:\Hearlium3_Next`.
2. Run `BUILD_HEARLIUM_INSTALLER.bat` there. If successful, install `installer\output\HearliumSetup.exe`.
3. Use disposable recordings. Confirm that new approval is blocked while an earlier accepted approval is being revoked; changing from Unsure to Rejected during rollback must not lose an `ACTION_REQUIRED` failure.
4. Confirm a completed rollback removes a matching pending marker, allowing a fresh *verified* analysis to be reviewed without an unrelated false approval-warning.
5. Disconnect the network while **Confirm & Save** sends a **non-learning** correction: the app must not create an unresolved learning-approval marker. Check saved review history before retrying.
6. With a pending feedback request active, verify **Analyze Recording / Reanalyze** decline to start a conflicting analysis.
7. For Android builds, commit the included Android files to **Branch 2** and build from that branch. The verified explanation must appear and the phrase “These sounds are not English words” must not return. Installing the Windows installer alone does not update the APK.
8. Only resume personalized learning after the applicable safety checks have passed. Never bypass an `ACTION_REQUIRED` audit.

**Development policy:** Main frozen, Phase 2 baseline protected, Branch 2 for changes, protected evidence, all storage/processing local to Windows Parent PC.
