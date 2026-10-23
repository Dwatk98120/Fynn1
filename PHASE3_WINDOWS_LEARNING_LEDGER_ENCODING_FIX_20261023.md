# Hearlium Branch 2 — Windows Learning Ledger Test Encoding Fix

Date: October 23, 2026  
Scope: Source-only regression-test correction for the full Phase 3 installer package

## Reported Windows build failure

In the full regression suite (Phase 2 + Phase 3), the test
`server/tests/test_phase3_learning_ledger.py::Phase3LearningTests::test_tampering_approval_blocks_learning_and_rollback`
failed with `UnicodeEncodeError: 'charmap' codec can't encode character '\u0254'`.
The test explicitly **read** a UTF-8 JSONL learning file, but wrote its deliberately tampered
copy without an encoding. Windows commonly defaults to CP1252 for that text operation;
the International Phonetic Alphabet character `ɔ` is not representable in CP1252.

## Changes

1. `server/tests/test_phase3_learning_ledger.py`: explicitly write UTF-8 in
   `test_tampering_approval_blocks_learning_and_rollback`. **No production learning code was changed.**
2. `server/tests/test_phase3_windows_text_encoding_guard.py`: add an automatic AST-based
   regression check to flag any future `Path.read_text()` / `Path.write_text()` usage
   in source tests that omits an explicit encoding.
3. Retain the earlier Windows UTF-8 **read** fix, all prior Phase 3 source repairs,
   Android phoneme explanation, and Android Live Recording removal.

## Verification performed

- `python -m pytest -q server/tests` — **144 passed, 8 subtests passed**.
- `LC_ALL=C LANG=C PYTHONUTF8=0 PYTHONCOERCECLOCALE=0 python -m pytest -q server/tests`
  — **144 passed, 8 subtests passed** in an ASCII-default-encoding simulation.
- Full ZIP integrity checked after packaging.

The Windows installer and Android APK have **not** been compiled in this environment.
The previous outstanding learning-reconciliation request-ID safety bugs remain separate
backlog items, not incorporated into this narrowly scoped Windows test fix.

## Windows installer instructions

1. Keep a copy of the last known-good ZIP and installed program.
2. Extract this ZIP into a **new** folder.
3. Run `BUILD_HEARLIUM_INSTALLER.bat`.
4. Confirm **all regression tests pass** before the installer build proceeds.
5. If another failure occurs, preserve the command output and report the complete failing test and traceback.

Frozen Main and protected Phase 2 baselines are unchanged. Work remains on Branch 2.
