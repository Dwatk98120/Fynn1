# Hearlium Branch 2 — Phase 3 Windows Regression-Test Encoding Hotfix

Date: 2026-10-23

## Why the Windows installer stopped

The installer build runs `python -m pytest -q server\tests` as a hard gate before compiling the Windows installer. On Windows, the default text encoding can be CP1252. The Android source includes UTF-8 phonetic symbols and other Unicode characters. The test `test_android_live_recording_removed_without_removing_regular_capture` called `source.read_text()` without an encoding, causing a `UnicodeDecodeError` (CP1252 byte 0x8F) before its assertions could run.

This is a test-file text-decoding failure, **not proof of a broken Android recording feature, speech recognizer, or learning engine**. It blocked installer creation by failing the pre-build test gate.

## Changes in this package

- In `server/tests/test_phase3_feedback_rollback_reliability_hotfix.py`, explicitly read both `MainActivity.kt` and `activity_main.xml` as UTF-8.
- Specify UTF-8 for the same test module's JSON audit-file read.
- In `server/tests/test_phase3_learning_ledger.py`, explicitly read saved JSONL ledger and revocation files as UTF-8.
- No application code, installers, server behavior, Android UI, or model files were changed. This full package retains the Phase 3 learning-reconciliation fixes and Android Live Recording removal from the prior hotfix.

## Validation

- All test files checked for `Path.read_text()` calls with no encoding: none remain.
- `python -m unittest discover -s server/tests -q`: 123 tests passed.
- `python -m pytest -q server/tests`: 143 tests and 8 subtests passed.
- Final ZIP compared against preceding complete hotfix to confirm only two existing test files changed, plus this new release note.

## How to rebuild on Windows

1. Keep a backup of your last known-working Hearlium build and recording data.
2. Extract this complete replacement ZIP to a NEW folder. Do not place the ZIP itself on GitHub or merge into Main.
3. Run `BUILD_HEARLIUM_INSTALLER.bat` from that extracted folder.
4. The full Phase 2 + Phase 3 test gate should no longer fail on CP1252 reading the Android Kotlin source. Other platform/dependency issues may still need independent attention.
5. Only after the installer is built, install and verify on Windows with disposable recordings.

### Notes

The two *later reported* learning-reconciliation findings (older example clearing a newer approval without exact request-ID matching, and retrying local reconciliation for an already-revoked example) are **not part of this Windows encoding repair**. They remain on the next Branch 2 hotfix backlog. Main and the earlier verified baseline remain untouched.
