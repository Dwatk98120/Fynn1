# Branch 2 — Phoneme IPA and Android display repair

- Android: display independent Faster-Whisper English words above raw phonemes, with explicit status if the recognizer provides no text.
- Phoneme classification: support IPA affricate aliases ʧ/ʤ and tie-bar equivalents without changing stored raw symbols.
- Word boundaries: suppress speculative merges across a standalone /aɪ/ pronoun.
- New focused regression tests.
- Main and original recordings are not modified. No caregiver learning is automatically approved.

## Limitations
This is a targeted source patch, **not** a new trained phoneme model. Actual acoustic recognition quality and Android UI require validation on the Windows Parent PC and a newly compiled APK.
