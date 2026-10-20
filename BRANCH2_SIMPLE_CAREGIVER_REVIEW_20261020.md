# Branch 2 — Simple Caregiver Review (2026-10-20)

## Changes
- Parent PC Record & Analyze: editable suggested sentence, **Confirm & Save**, **Not Sure**, **Reject**, and advanced word-level review.
- Android caregiver review: single editable suggestion dialog with the same three choices; removes the multiple-menu workflow.
- API accepts an explicit `review_decision` for confirmed, unsure, or rejected feedback and persists it in append-only feedback records.
- Sentence confirmation saves caregiver feedback with `approved_for_learning=false`. Individual phoneme/word learning requires separately validated word-level alignment and explicit approval.
- Original recordings, observations, and interpretation hypotheses are not rewritten.

## Build and test
- Python compileall: passed.
- Selected server regression tests: 11 passed.
- APK and Windows installer: not compiled or runtime-tested in this environment.

## Build instructions
- Keep Main frozen. Commit source contents to `hearlium-parent-pc-integration`.
- Run the existing GitHub Actions Android debug APK workflow.
- Run `BUILD_HEARLIUM_INSTALLER.bat` on the Windows build PC.
- Install both updates, analyze a test recording, edit the sentence, save it, and verify the feedback appears in recording history.
- Check Not Sure and Reject do not approve learning, and verify advanced word review remains accessible.
