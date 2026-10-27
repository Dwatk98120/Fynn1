# Branch 2 — Consonant accuracy regression package (2026-10-26)

This release adds a **read-only regression test tool**, not a retrained model or a demonstrated recognition-accuracy fix. The user-provided 18-word adult test exposed Faster-Whisper's substitutions (13/18 exact words) and Wav2Vec2's final-consonant and initial-consonant mistakes. Do not confuse internal phoneme confidence with validated accuracy.

## Run

From the source root: `python phase3_consonant_regression.py "PATH_TO_FULL_ANALYSIS.json" --output consonant_report.json`

Run verification: `python -m unittest -v test_phase3_consonant_regression.py`

The tool accepts full Parent PC analysis JSON with `analysisResult` or a direct analysis result. It aligns the fixed 18-word test order, scores exact word recognition, and shows phoneme strings side by side for human review. It does **not** infer whether a speaker has a speech difficulty, modify recordings, correct word boundaries, approve examples, or learn automatically. Do not use on unrelated recordings as a general-purpose accuracy score.

## Next production engineering work (not included)

1. Benchmark initial /θ/, /t/, /f/, /ʃ/, /tʃ/, /k/ confusions with additional adult test recordings and, later, separately consented pediatric data.
2. Add validated per-word phoneme alignment and avoid treating CTC character chunks as verified word boundaries.
3. Hold missing-final-consonant alerts as *unverified* until acoustic evidence, independent recognition, and caregiver review agree.
4. Calibrate confidence against a protected labeled corpus. Preserve the original 13-layer pipeline and original observations.

Main must remain frozen; apply on Branch 2 only. Build and installer validation on Windows are still required.
