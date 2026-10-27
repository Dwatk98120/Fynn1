# Branch 2 Phase 3 — Word timestamps and boundary review

Changes:
- Enable Faster-Whisper `word_timestamps=True` and retain individual estimated word intervals within existing ASR segment records.
- Add non-destructive boundary proximity review candidates to `wordPhonemeAlignmentReview`.
- Maintain abstention when word timings are unavailable or phoneme-to-word overlap is ambiguous.
- Never confirm a pronunciation error or authorize learning based on timestamps, overlap, or consonant proximity.
- Do not modify original WAV files or protected observations. No changes to Main.

Limitations:
- Word timestamps are estimated by Faster-Whisper and may be inaccurate, especially with overlapping speech, atypical articulation, or quiet consonants.
- This improves visibility and review safety, NOT the underlying phoneme model's recognition accuracy. Model-level consonant recognition remains a separate future task.
- Windows packaged installer and live 13-layer regression testing remain pending.

Verification: `PYTHONPATH=. pytest -q server/tests/test_phase3_word_phoneme_alignment_safety.py server/tests/test_phase3_word_timestamp_boundary_repair.py`
