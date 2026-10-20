# Branch 2 word ranking and Android diagnostics — 2026-10-20

## Confirmed cause
The 2026-10-20 analysis JSON contains `wordRecognition.text = "I want a cookie."` while `transcript` contains raw phoneme CTC output. These are independent outputs and must not be interchanged.

## Changes
- Expanded general conversation lexicon with pronouns, determiners and common verbs (no model retraining).
- Deduplicated identical candidate words; suppressed low-similarity long phoneme candidate matches (e.g. `sloʊki` -> `see`).
- Kept weak or ambiguous matches review-only. Did not change original observations or the approved-learning workflow.
- Added Android English-first display and build diagnostic marker; supported an additional nested `result.wordRecognition` response shape.

## Device validation
1. Rebuild APK from this package and install the newly generated artifact.
2. Verify the status includes `English + sounds (Branch 2)` and results include `Display build: Branch 2 English-first repair`.
3. If the old `PC received and analyzed recording` / `Heard:` UI still appears, check that the device is running the newly built APK and that this is the same screen/path; the pictured old UI string is absent from this source tree.
4. Verify Parent PC JSON has `wordRecognition.text` and phoneme `transcript` separately. No transcription must be fabricated when missing.
5. Build Windows installer with existing project scripts; validate a live recording before treating changes as production verified.

## Limits
Source and Python tests only; no Android or Windows binary was compiled here. Phoneme confidence is not word-recognition accuracy. No new trained model is bundled.
