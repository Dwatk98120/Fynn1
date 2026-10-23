# Hearlium Branch 2 — Phase 3 Exact Request Reconciliation + Retry

**Date:** October 23, 2026  
**Baseline:** Hearlium_Branch2_Phase3_Learning_Reconciliation_Android_NoLive_Hotfix_20261023.zip  
**Branch:** hearlium-parent-pc-integration only. **Main remains frozen.**

## Repairs

1. **Precise approval reconciliation.** The learning server accepts an optional `client_request_id`, records it in hashed feedback/approval ledger entries, and includes the original ID in Learning History. Parent PC records this ID in each approved example reference and compares exact request IDs when resolving a manual rollback. An older example cannot clear the warning for a newer pending request just because both share a recording and observation.
2. **Retry after a partial rollback.** The Learning History action is now **Revoke / reconcile selected example**. It also works for an example already marked REVOKED on the server, using the idempotent rollback API and retrying local recording reconciliation.
3. **Audit integrity.** Missing or conflicting IDs leave ambiguous approvals blocked. The original audio, observations and historical ledger remain untouched. Repeated reconciliation preserves an existing revocation timestamp.

## Build and use

- Windows installer definition: **0.4.5**. This is a full **source ZIP**, not a precompiled EXE.
- Android source remains **3.3 / versionCode 6** with Live Recording removed and normal recording/upload retained. The Windows installer does not replace an Android APK.
- Build the Windows installer with `BUILD_HEARLIUM_INSTALLER.bat` on a Windows build PC. Build Android using the **Hearlium Android APK - Verified Gradle 8.9** GitHub workflow on Branch 2, not the main-only workflow.
- Confirm the rebuilt Android APK is 3.3/code 6, not the stale 3.2/code 5 APK. Back up app-private recordings before uninstalling any APK.
- Back up `%LOCALAPPDATA%\Hearlium\ParentPC` before installing. Verify with **disposable recordings** and do not bypass `ACTION_REQUIRED`.

## Compatibility and cautions

- Android and legacy clients can omit the new optional request field.
- Older examples without an exact request-ID link may require manual investigation; ambiguous warnings intentionally remain blocked.
- The package does not include any student data, server model weights, APK or compiled Windows installer. No Render/cloud service is added.
- Python regression tests, syntax checks, Android source assertions and ZIP CRC are the supported build checks. Windows Inno compilation, Android Gradle compilation and real-device testing still require their respective environments.

## Files modified

- `server/learning_store.py` and `server/main.py`
- `parent_pc_local/direct_recording.py` and `parent_pc_local/phase3_learning_gui.py`
- `server/tests/test_phase3_learning_ledger.py` and `server/tests/test_phase3_feedback_rollback_reliability_hotfix.py`
- `installer/Hearlium.iss`, `BUILD_VERSION.txt`, `HOTFIX_CHANGED_FILES.txt`
