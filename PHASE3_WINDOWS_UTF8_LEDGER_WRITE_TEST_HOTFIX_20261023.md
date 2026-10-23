# Hearlium Branch 2 — Windows UTF-8 Learning Ledger Test Write Fix

Date: October 23, 2026

## Reported Windows failure

The installer builder's Python regression test `test_tampering_approval_blocks_learning_and_rollback`
raised `UnicodeEncodeError` after reading the learning ledger with UTF-8 and then
writing the tampered fixture using Windows' default cp1252 encoding. The fixture
contains IPA phoneme characters (for example `ɔ`) that cp1252 cannot encode.
This made the builder stop with one failed test even though the application itself
was not responsible for this failure.

## Repair

- Specify `encoding='utf-8'` for the learning ledger test's `Path.write_text`
  call, preserving the intended tamper-detection test behavior.
- Review all `Path.read_text`, `Path.write_text` and text-file `open` calls
  in the Python test suite; no additional implicit-encoding uses remain.
- Preserve the earlier Android-source UTF-8 read fix and all Phase 3 data
  integrity, request-ID reconciliation, caregiver review and Android no-live work.

## Build notes

- Full Branch 2 source archive. This ZIP is not a compiled EXE or APK.
- Windows Inno Setup version: 0.4.5. Android: 3.3 (code 6).
- Extract into a new folder and run `BUILD_HEARLIUM_INSTALLER.bat`.
- Main and the protected working baseline remain untouched; all services run
  locally on the Windows Parent PC.
