# Hearlium Branch 2 — File Integrity Reanalysis Guard (0.4.9)

## Changes
- Parent PC main window displays version and hotfix identifier.
- Reanalysis jobs cannot reuse earlier ordinary analysis or earlier reanalysis sessions.
- Local server reports `recordingStorage.reused`, `source=reanalysis`, and original WAV path.
- Parent PC rejects reanalysis results without explicit storage-reuse acknowledgement.
- No existing recordings, metadata, or caregiver approvals are changed by the patch.

## Limitations
This is a targeted code fix, not proof the reported duplicate creation is resolved.
A real Windows installed-app test is required. The guard detects an unacknowledged write
but cannot undo a WAV already created by an outdated or alternate server path.
Do not delete existing duplicates. Main frozen; Android unchanged.

## Windows acceptance test
1. Preserve/backup all recordings; close old Parent PC and server processes.
2. Build installer using BUILD_HEARLIUM_INSTALLER.bat and install.
3. Verify main UI shows Build 0.4.9.
4. Record SHA256 count for existing test recording before reanalysis.
5. Click Recording History > Reanalyze once. Check result and logs.
6. Recount identical WAVs; count must not increase. Repeat once.
7. Verify original SHA256 unchanged, history and approvals unaffected.
If any count increases, stop testing and retain all files.
