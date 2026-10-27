# Hearlium Branch 2 — Word/Phoneme Alignment Safety Hotfix (2026-10-26)

## Changes
- New `server/word_phoneme_alignment_review.py` emits an interpretation-only `wordPhonemeAlignmentReview` field.
- Never assigns phonemes to individual words using only Faster-Whisper utterance-level timestamps.
- If explicit word-level timestamps are present, emits tentative timing-overlap candidates only when overlap is unique; ambiguous cases remain unresolved.
- Always marks word-level pronunciation errors unverified, forbids automatic consonant-error attribution, and disallows learning authorization from alignment.
- Raw observations, WAV files, existing interpretations, approval logic, and 13 layers remain unchanged.

## Verification
`python -m pytest -q server/tests/test_phase3_word_phoneme_alignment_safety.py server/tests/test_phase3_phoneme_disagreement_20261026.py`
Result: 8 passed.

## Deployment
Source ZIP only. Apply/build on Branch 2; keep Main frozen. Back up working source and user evidence. Reanalyze protected adult test recordings on Windows, compare output and review UI, and confirm no change to learning permissions. No model weights were changed. This release does not improve underlying phoneme recognition or add precise word timestamps.
