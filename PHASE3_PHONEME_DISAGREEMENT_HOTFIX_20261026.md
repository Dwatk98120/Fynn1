# Hearlium Branch 2 — Phoneme Disagreement Hotfix (2026-10-26)

## Changes
- Recognize legacy IPA affricate symbols (ʧ, ʤ, ʨ, ʥ) as their canonical counterparts for phoneme classification, preserving original observed symbols.
- Normalize the same symbols for phoneme tokenization and recognizer comparison only; acoustic evidence is not rewritten.
- Flag moderate independent word/phoneme agreement below 0.85 for caregiver review; existing severe disagreement threshold below 0.50 remains. This is a conservative *review threshold*, not validated phoneme accuracy, diagnosis, or learning permission.
- Add four model-free regression checks. Preserve all existing recordings, analyses, approval and learning controls.

## Verification
- Python unittest discovery: 284 tests, OK, 3 skipped (Linux environment; not a Windows installer test).
- Existing Windows runtime, bundled models, actual recording reanalysis and installer build have **not** been validated here.
- This hotfix does not retrain or alter the phoneme model; observed initial/final consonant errors may persist. Word-boundary timing and calibrated confidence require separate measured model/recording work.

## Install/build
This is a full source ZIP intended for the existing Branch 2 GitHub/Windows build workflow. Review changes, build using the repository's existing workflow and Inno Setup instructions, then test on a non-production installation before distribution. Main remains frozen. Back up your working Branch 2 baseline. Do not overwrite existing recording data.
