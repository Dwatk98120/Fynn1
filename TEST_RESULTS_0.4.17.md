# Hearlium 0.4.17 Tk repair source validation

This is a source-only Branch 2 handoff. It includes the 0.4.17 legacy-checksum
reanalysis repair and the subsequent Windows Tk packaging repair. It excludes
the in-development 0.4.18 phoneme/capture hotfix.

- Staged source regression suite: **356 passed, 3 skipped**, 2026-10-27.
- All **27 program/source files** covered by the tested 0.4.17 Tk build stamp
  match that stamp byte-for-byte. See SOURCE_RELEASE_0.4.17_VERIFICATION.json.
- The corresponding frozen executable SHA-256 was verified separately:
  `25796c976001f135a59f08ccfa8390b44c19da060ea6d973195038a325217f61`.
- The existing corrected installer, built and verified earlier, is named
  `HearliumSetup-0.4.17-TkRepair.exe`, SHA-256
  `fca44d4d7a88540844a468efd26eb0eec9997c251d376215a0a03928560a66dc`.
  The installer and executable are intentionally absent from this source package.
- That frozen build passed GUI hidden-window, server import, Layer 2, Android
  retry/storage, legacy reanalysis guard and packaging-integrity checks.
- No installation, device acceptance, Git commit, push or remote change was
  performed by preparing this handoff.

The source suite used the isolated build Python and separate temporary
application data. No production recordings, metadata or historical results
were changed. Optional private-audio tests remain skipped.

Installed-device checks remain pending: protected reanalysis with original-WAV
counts/hashes, actual Android retry/network interruptions, offline inference
and restart, caregiver approval/revocation reconciliation, and reinstall data
preservation using disposable test data. Android remains 3.3.3/code9.
