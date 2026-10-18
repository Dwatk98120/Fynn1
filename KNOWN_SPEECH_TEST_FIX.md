# Known Speech Test / Phoneme Output Label Fix

Select **Analyze speech**, check **Known Speech Test: counting 1 to 12**, then **SEND & ANALYZE ON PC**. The PC must be updated from this same ZIP.

## What changed
- Android no longer labels phoneme CTC output as recognized words in the main analysis results.
- Explicit opt-in counting test transmits a context marker; the server returns a separate, non-learning diagnostic field.
- Expected numbers are not substituted into the observed output; no fake word accuracy is reported.
- Suspected consonant omissions are marked as unverified candidates.
- Record identifiers appear at the bottom of the result, separate from observations.

## Limitations
This patch does **not** add a word-level speech-to-text model or prove improved accuracy. It diagnoses a misleading display and establishes a safe test harness. Full word accuracy requires a separate word ASR engine and audio-grounded alignment. Existing non-test context remains unchanged.

## Build
Push the contents to your GitHub repository and run the existing Android APK workflow. Rebuild/restart the Parent PC service from the same source for the diagnostic response field. No Android Studio required.
