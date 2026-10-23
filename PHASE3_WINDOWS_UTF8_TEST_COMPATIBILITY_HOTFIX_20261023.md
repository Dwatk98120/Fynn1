# Hearlium Branch 2 — Windows UTF-8 Regression Test Compatibility

Date: October 23, 2026

## Reported failure

During a Windows installer build, \`server/tests/test_phase3_feedback_rollback_reliability_hotfix.py\`
failed in the Android no-live source assertion with:

\`UnicodeDecodeError: 'charmap' codec can't decode byte 0x8f\`

The test used \`Path.read_text()\` without specifying the encoding. Windows Python
can default to the active ANSI code page, while the Kotlin source contains
UTF-8 phoneme symbols. The original source and recording features were not at fault.

## Repair

- Read Kotlin and XML source in the no-live regression test with \`encoding='utf-8'\`.
- Explicitly decode the test's JSON audit and approved-learning ledger fixtures as UTF-8.
- Keep all previously integrated Phase 3 request-ID, reconciliation, caregiver,
  Android no-live and installer fixes intact.

## Build and verification

- Full source ZIP; not a compiled installer or APK.
- The Parent PC Inno version remains **0.4.5**; Android remains **3.3/code 6**.
- Use \`BUILD_HEARLIUM_INSTALLER.bat\` in this extracted new source folder.
- The build's Python regression suite must pass before the installer is created.
- Keep Main and the last working baseline untouched. All server and learning
  services remain on the local Windows Parent PC.

The change is restricted to test-source text decoding and release notes.
