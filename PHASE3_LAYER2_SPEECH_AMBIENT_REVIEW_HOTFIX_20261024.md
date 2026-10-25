# Hearlium Branch 2 — Layer 2 Speech-versus-Ambient Review (24 October 2026)

## Real-world problem

David recorded a short sentence followed by ambient sounds. The previous
Layer 2 v2 run, lasting 17.316 seconds, reported six separated energy islands
and correctly declined to assert a definite speech endpoint. However,
acoustic energy alone could not distinguish the short utterance from subsequent
ambient sounds.

The corresponding JSON provides an independent clue:

- Faster-Whisper's unverified word candidate segment ended at 8.30 seconds.
- The phoneme recognizer still produced candidate sounds until 17.276 seconds.
- Last measured energy activity was at 17.10 seconds.

The disagreement is **not proof** that everything after 8.30 seconds was
ambient noise: either engine may be wrong. Original WAVs were not provided,
and transcription accuracy is not validated. Only the JSON evidence was used
to design deterministic regression tests.

## Cumulative changes in this hotfix

1. Preserve original audio and the previous Layer 2 v2 sound-island metrics
   and missing-consonant evidence guards, unchanged.
2. Add `server/speech_activity_review.py`, an independent, deterministic
   **interpretation-only** check using existing Faster-Whisper segment times,
   CTC phoneme candidate times, and the last observed energy-activity time.
3. Return a separate `analysisResult.speechActivityReview` in saved analysis:
   - `reviewVersion: layer2-speech-ambient-crosscheck-v1`
   - `wordAsrEndSeconds`, `phonemeCandidateEndSeconds`,
     `endDisagreementSeconds`, `lastEnergyActivitySeconds`
   - `possibleLateSoundBeyondWordAsrSeconds`
   - `candidateSpeechEndSeconds` only when independent models approximately
     agree, always unverified and requiring caregiver review
   - explicit `ambientSoundConfirmed: false`, `speechEndVerified: false`,
     `humanReviewRequired: true`, `learningEligible: false`, and
     `changesProtectedObservation: false`.
4. Display disagreement and uncertainty in the Windows Parent PC Evidence UI.
5. Update frozen EXE self-check and build source-integrity verification so
   compiling an old executable does not silently omit the feature.
6. Add deterministic synthetic and JSON-timing regression tests.

## Validation on the user's Windows PC

1. Extract the **entire** ZIP to a new, short path and run
   `BUILD_HEARLIUM_INSTALLER.bat` (not `COMPILE_INSTALLER_ONLY.bat`).
2. Install the newly generated Setup EXE. Restart Hearlium and its local API.
3. Reanalyze the 17.316-second adult reference recording with known ambient
   sounds, exporting **new** Raw JSON instead of opening an older saved review.
4. Check `speechActivityReview.reviewVersion` and whether the API reports
   a large recognizer timing disagreement, candidate endpoint null, and
   `ambientSoundConfirmed: false`.
5. Check the original WAV hash is unchanged, previous observation history
   remains present, and no approval/learning occurs automatically.
6. Compare with another short, quiet adult recording and a two-phrase adult
   recording to gauge false positives; do not mark accuracy validated yet.

## Boundaries

The new review flags **possible ambient noise** but does not classify it as
fact. Faster-Whisper can hallucinate words and phoneme CTC can decode ambient
noise as phonemes. Neither model's timestamps are known ground truth.
The cross-check never changes immutable observations, transcript, audio,
consonant findings, or caregiver learning. It uses the same local Windows
models; no hosted service, new heavy dependency, or Android code change.
Main remains frozen; Branch 2 only.
