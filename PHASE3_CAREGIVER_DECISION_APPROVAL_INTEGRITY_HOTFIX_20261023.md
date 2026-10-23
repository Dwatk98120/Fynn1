# Hearlium Branch 2 — Phase 3 Caregiver Decision & Approval Integrity Hotfix

**Date:** 2026-10-23  
**Baseline:** `Hearlium_Branch2_Phase3_Analysis_Feedback_Consistency_Hotfix_20261023.zip`  
**Scope:** Windows Parent PC caregiver feedback integrity only. No Android source or model changes.  
**Main and Phase 2:** not changed.

## Fixed — critical review and learning safety regressions

1. **Older approval cannot overwrite a newer caregiver decision.** Every new simple-caregiver decision, including a submitted feedback request, advances a per-recording `reviewRevision` stored in the recording metadata. The API response is applied only if both the current observation ID and revision match the request. A rejection/unsure action advances the revision *under the existing metadata lock*. Delayed callbacks also re-check the revision before updating the visible review status.
2. **Superseded accepted approvals are revoked when possible.** If a previously submitted approval is accepted after a newer decision, the Parent PC records the actual server response in an audit file and invokes the **local-only** `/v1/learning/revoke` endpoint using the returned learning `exampleId`. The API already implements versioned, append-only revocation. A newer Rejected or Unsure decision also triggers revocation of an approval that was already stored locally. If revocation cannot be confirmed, the application **does not claim success**, retains an `ACTION_REQUIRED` audit record, and tells the caregiver to verify/revoke that example in Phase 3 Learning History.
3. **Metadata observation ID alone cannot authorize feedback.** Before building the feedback payload, the Parent PC requires a complete in-memory result that matches the verified, currently saved analysis for the selected recording. Invalid, stale, unloaded, or mismatched results block feedback, even if old metadata still has an observation ID. The check is repeated under the metadata lock when the submitted revision is reserved.
4. **Lost feedback responses remain visible as unresolved.** A network timeout can occur after the API accepted a request. Pending or superseded approvals leave persistent metadata markers and a local audit entry. The Parent PC will block *new approval submissions* while the outcome is unresolved, rather than guessing or retrying automatically. Unsure/Reject remain available. The review screen shows a Learning History warning when an unresolved decision is reopened.
5. **Original recordings and prior evidence stay intact.** Nothing here edits WAV audio, rewrites original observations, automatically approves an old analysis, or triggers retraining. Existing API diagnostics, student library, Android wording, and earlier Phase 3 fixes are retained.

## Locations and manual recovery

- **Local feedback audits:** `%LOCALAPPDATA%\Hearlium\ParentPC\feedback_observation_audit\`
- **Learning history and rollback:** Parent PC window → **Phase 3 Learning History**.
- If an audit entry says `revocationStatus: ACTION_REQUIRED`, the old approval **may still be active** on the learning server. Verify/revoke the example ID in Learning History before using personalized learning or resubmitting approval. Do not delete the audit files or duplicate the feedback request.

## Verification performed here

- `PYTHONPATH=.:server:parent_pc_local pytest -q server/tests`: **125 passed; 8 subtests passed**.
- `PYTHONPATH=.:server:parent_pc_local python -m unittest discover -s server/tests -p 'test_*.py' -q`: **105 passed**.
- `xvfb-run -a python phase3_consistency_ui_smoke.py`: **passed** (Android analysis load, recording search and stale result invalidation).
- `python -m compileall -q parent_pc_local server`: **passed**.
- ZIP archive integrity check: verified during packaging.

New tests simulate delayed approval followed by Reject or Unsure, approval already committed then rejected, lost/failed rollback, deferred GUI callback, invalid/no loaded analysis, stale observation, interrupted response, and safe default after uncertain network failures.

**Not yet verified:** Windows Inno Setup installer compilation, live API/device behavior, and prolonged dropouts. The known random API connection issue remains open. Simulated fault tests are not a substitute for controlled real-PC testing with disposable recordings. In particular, crash recovery after the server accepts an approval but before its reply is received can require **manual Learning History reconciliation**.

## Build

1. Extract the complete ZIP to a clean short Windows folder such as `C:\Hearlium3`, keeping previous installer and source backups.
2. Run `BUILD_HEARLIUM_INSTALLER.bat` in the extracted folder.
3. When compiled, install `installer\output\HearliumSetup.exe` and use disposable test recordings for validation.
4. Verify that Rejected/Unsure never reverts when a delayed approval returns, and that no submission is possible when no verified analysis is loaded. Test the local History and revocation status independently.
5. Do **not** promote Phase 3 personalized learning until the live safety checks and intermittent API issue have been resolved.

Keep development on Branch 2, Main frozen and Phase 2 protected. No repository branch was modified when creating this source ZIP.
