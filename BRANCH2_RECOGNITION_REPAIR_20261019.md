# Branch 2 Recognition Repair — source build

Based on Hearlium_Branch2_Homophone_Learning_Source_20261019(1).zip. Main not modified.

Changes:
- Expanded candidate dictionary to include there, their, they're, are, is, was, were, cookie, cookies, left, leave, no, know.
- Reject candidate segment merges when their best ranking does not exceed the best individual segment ranking. Preserve raw CTC boundaries.
- Added negative-determiner and knowledge-verb contextual homophone hints (ranking only, never acoustic evidence).
- Recognize `o` as a diphthong component in phoneme feature reporting; unknown symbols no longer display as `clear`.
- Added `recognizerAgreement` in JSON comparing the Faster-Whisper word hypothesis with independent phoneme CTC output. This is NOT verified accuracy or ground truth.
- Added 5 targeted regression tests.

Limitations: No model inference or Windows installer/APK compiled in this environment. No verified live recording benchmark. Pronunciation matching and calibration still need real audio testing. Existing `phonemeComparison` field remains unchanged. Caregiver approval is still required for learning.

Build on Windows using the existing repository build scripts. Keep Main frozen and apply only to Branch 2.
