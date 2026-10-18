> HISTORICAL NOTE: This document may describe an earlier PyAV/Faster-Whisper build. The current no-PyAV build excludes both packages and disables independent word ASR. See NO_PYAV_BUILD_NOTES.md.

# Hearlium word recognition and confidence repair — October 18, 2026

This source update is based on the ParentPC Installer Dependencies Fixed ZIP.

- Retains independent faster-whisper word transcription and phoneme CTC observations.
- Makes absent single-word candidate confidence `null` rather than incorrectly showing 0.00.
- Labels candidate ranking scores as heuristic, not word-recognition probabilities.
- Suppresses consonant-deletion flags on multiword/unsegmented or low-scoring recordings.
- Adds explicit `deletionLearningEligible: false` and review status metadata.
- Updates Android analysis display to explain missing confidence and unverified findings.
- Retains the tested `av==16.1.0` dependency and existing installer build scripts.

## Test
1. Extract the complete ZIP into a NEW directory, not over an old build.
2. Run BUILD_HEARLIUM_INSTALLER.bat, following its existing prerequisites.
3. Install the newly generated Parent PC setup; rebuild/install the Android APK from this same source if you want the revised display.
4. Reconnect on the same Wi-Fi and record counting 1–12.
5. Verify that `WORD RECOGNITION` shows a candidate transcript or a clear error/status, `RAW SOUND OBSERVATION` remains separate, and multiword recordings do not show false 0.00 candidate confidence.

This update is syntax-checked for Python but has NOT been run end-to-end on Windows/Android. Human confirmation is still required for speech-pattern learning. It does not establish word recognition accuracy.
