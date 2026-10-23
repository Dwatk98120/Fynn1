# Hearlium Phase 3 — Caregiver Word Review Usability Hotfix (Branch 2)

## Why this hotfix exists
The older review window warned "Segment 0: use one word and resolve uncertain boundaries before confirming." This was confusing because caregivers have no manual boundary editor in the current application. An identified word (such as **a**) can still be blocked because its *clip timing* is uncertain. An uncertain clip must not be approved merely because someone recognizes the word.

## Changes in this build
- Displays **Word 1, Word 2, ...** instead of zero-based segment numbers.
- Provides clear four-part instructions and separate **Play clip** / **Correct** actions.
- Caregiver choices display as **Not reviewed / Confirm / Unsure / Reject**. Existing storage statuses (`not_reviewed`, `confirmed`, `boundary_uncertain`, `rejected`) are unchanged.
- **Correct** focuses/selects the word field. Editing an already confirmed word automatically changes it to **Not reviewed**, requiring a fresh explicit confirmation.
- Replaces generic confirmation-block warning with exact reason (missing word, multiple words, invalid label, unclear timing, adult reference).
- An actionable **Review Word N** control scrolls to and highlights the specific word; **Mark Unsure** changes only that row's selection. The caregiver then clicks **Save reviews** to save.
- All rows are validated **before** any approved clips are exported, preventing an invalid later row from creating partial approved exports during that save attempt.
- Approved clips remain evidence only; no automatic model retraining.
- Does not modify API monitoring, raw WAVs, analysis, rollback, Android source, or installer workflow.

## Critical evidence safeguards
- A word with automatically flagged unclear beginning/end **cannot be confirmed** in this screen. Choose **Unsure** or **Reject**, or collect a clearer recording / await a separate boundary editor. Listening to the clip does not automatically clear the flag.
- An adult reference cannot be approved for child-specific learning.
- Only one syntactically valid word can be confirmed (as in the prior implementation).
- A corrected word is not automatically approved.
- The saved review schema and existing per-recording review location are retained.

## Build
1. Extract the **complete** ZIP into a **new short folder** such as `C:\Hearlium3`.
2. Run `BUILD_HEARLIUM_INSTALLER.bat` on Windows with Python 3.12 / Inno Setup 6 installed.
3. After a successful build, locate `installer\output\HearliumSetup.exe`.
4. Back up the prior stable installer and test with a known recording. Do not merge changes into Main.

## Validation performed for source package
- Python syntax compilation for changed modules.
- All 67 tests in `server/tests` passed under pytest, including the existing Phase 3 API diagnostics checks and 4 new caregiver-review checks.
- `python -m unittest discover` passed 47 checks.
- Windows PyInstaller and Inno Setup compilation must be performed on the Windows build computer; no installed runtime stability is claimed.

## Existing limitation
The review dialog is **not** an audio waveform boundary editor. To confidently approve algorithm-flagged words, better segmentation or explicit boundary correction will be a separate verified feature. The API disconnect root cause remains under investigation with the Phase 3 diagnostics hotfix.
