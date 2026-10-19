# Hearlium Branch 2 — Homophone interpretation source build

Based on Hearlium_Branch2_Android_Caregiver_Review_Complete_Source_20261019.zip.

## Added
- server/homophone_engine.py: homophone candidate generation and conservative sentence-local grammar ranking.
- server/main.py: returns a separate `homophoneReview` field alongside `wordRecognition`, without overwriting the original transcript, immutable observation, or raw audio.
- server/tests/test_homophone_engine.py: six tests for context, uncertainty, history, and evidence separation.

## Existing caregiver feedback
- Existing `/v1/learning/feedback` endpoint remains unchanged. Only explicitly approved single-word examples can update a speaker profile; multiword feedback is not trained as one word.
- The Android app's existing caregiver correction workflow remains intact. This release does NOT add a dedicated homophone selection UI, nor does it automatically apply homophone suggestions to the Android main results screen.

## Limitations
- Rule-based grammar cues are deliberately conservative; these are suggestions, not verified intended meanings or calibrated probabilities.
- `context` is recorded as context provenance but this first version only uses adjacent recognized words for ranking, not arbitrary caregiver-supplied context.
- Homophone review is returned only when Faster-Whisper provides text. If ASR is unavailable, the review is empty.
- No model retraining, auto-confirmation, or cloud service.
- Windows installer and Android APK were not compiled in this environment. Build and test on Branch 2. Main stays frozen.

## Verify
1. Build the Parent PC installer and install it on the test PC.
2. Record: 'I won the game', 'one two three', and an isolated 'one'.
3. Check Raw JSON `wordRecognition` and `homophoneReview` fields.
4. Ensure `observation` and `wordRecognition.text` remain unchanged after suggestions.
5. Verify existing caregiver correction/approval persists only after explicit approval.
