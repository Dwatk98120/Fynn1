# Branch 2 — Duplicate WAV storage safety (first implementation)

## Included
- Android API storage retries reuse an already completed original WAV **only** when recording ID, speaker ID, session ID, caregiver name and SHA-256 all match.
- Same recording identity with changed audio or name fails closed for caregiver/engineering review.
- A missing, corrupt or incomplete original fails closed; nothing is overwritten or deleted.
- Existing WAVs, JSON files, caregiver decisions, and evidence remain untouched.
- Regression tests: `python -m unittest discover -s server/tests -p test_phase3_android_idempotent_storage.py -v`.

## Important limitations
- Parent PC `parent_pc_api_` WAV duplication is **not repaired yet**. That pathway may represent a new recording or reanalysis, and needs metadata/provenance mapping before changing writes.
- This is not a full solution for simultaneous upload races across processes; use an atomic per-recording reservation/lock and durable index before production deployment.
- Existing duplicate WAVs are **not** consolidated, removed, or renamed.
- Target Voice Isolation is **not included**. It must remain deferred until the full storage repair and regression validation.
- Windows installer and full 13-layer live regression have not been run in this environment.

## Build and validation
Use the existing `BUILD_HEARLIUM_INSTALLER.bat` from this ZIP on Branch 2. Keep Main frozen and preserve the previous working installer as rollback. Do not delete or clean `%LOCALAPPDATA%\\Hearlium\\ParentPC`.
