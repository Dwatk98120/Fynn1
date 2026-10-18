Hearlium Speech Recognition Phase 1 — candidate segmentation and confidence repair

BASE: Hearlium_ParentPC_Analysis_500_FIX_Installer_Builder(1).zip (locally available complete build)
NOTE: This is not an exact checkout of GitHub Branch 2. GitHub connector was read-only.

Changes:
- Keeps the WAV-bytes temporal prosody fix (no undefined temp_path).
- Preserves individual CTC token confidences; no blanket average fallback.
- Adds conservative CTC blank-gap segmentation and separate segmentCandidates result.
- Adds common number words to general-purpose candidate dictionary.
- Recognizes r, a, c IPA symbols and flags unknown symbols as uncertain.
- Leaves raw phoneme observations immutable and learning subject to approval.
- Adds lightweight source regression tests in server/tests.

LIMITATIONS:
- CTC blank gaps do not equal word boundaries; fluent counting may not split well.
- This is not a new ASR model and does not guarantee word recognition.
- No known-answer labels were inserted into inference or learning.
- The whole-utterance candidates field remains separate from segmentCandidates.
- Requires real Parent PC runtime validation; no Windows installer built here.

To test: run python -m pytest server/tests/test_phase1_source_regression.py
Then rebuild Parent PC using existing build scripts and record a new counting sample.
