# Hearlium combined repair source build — 2026-10-17

This source ZIP combines the previously prepared **Four Analytics Repairs** and **Android-PC Verified Transfer Fix** packages.

## Included
- Android receipt-first transfer changes and Parent PC `/v1/recording-receipt` transport acknowledgement. Receipt is **not** a confirmation that AI analysis finished.
- Number-by-number review output (`numberReview`) retained alongside the four-repair pipeline's `wordSequenceReview` and `referenceAudioComparisons`.
- Segment-level caregiver learning approval safeguards; immutable phoneme observations retained.
- Evaluation accuracy counters only increment for comparable predictions.
- Existing Windows Bluetooth/.NET and Inno Setup source files retained from the four-repair package.

## Verification performed
- `python -m compileall -q server parent_pc_local` — passed.
- `PYTHONPATH=.:server pytest -q server/tests` — 20 passed.

## Not verified here
- No Windows .exe installer or Android APK was compiled in this Linux environment.
- No real phone-to-PC Bluetooth transfer or live model inference was exercised.
- GitHub Actions and Inno Setup build must be run on the target build system.

This ZIP is **installer source**, not an already-built Windows setup executable.
