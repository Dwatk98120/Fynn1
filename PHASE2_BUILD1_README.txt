HEARLIUM BRANCH 2 - PHASE 2 BUILD 1 (SOURCE)
Date: 2026-10-21
Base: Hearlium_Branch2_Recovery_Phase1_Startup_Installer_Fix_20261021.zip

CHANGES
- Review-only word boundary guard: when independent Faster-Whisper English words align 1:1 with CTC phoneme segments, do not propose merging two distinct recognized words. Example: I + want is no longer suggested as twenty.
- Normalize r/ɹ notation solely inside independent recognizer agreement comparison; original phoneme strings are unchanged.
- Added regression tests for the actual I want three cookies example, unaligned ASR, and r/ɹ equivalence.
- No changes to Android UI, installer, original audio, caregiver confirmation storage or learning policy.

VERIFICATION
- Python unit tests: 21 passed in this environment.
- Not yet validated with actual speech engines, Android APK, Windows frozen EXE, or Inno Setup installer.

INSTALL
- Import this ZIP as source to Branch 2 ONLY. Do not merge into Main.
- Run Windows installer build using the existing project instructions, then test on a separate installation/test system without overwriting the working Phase 1 deployment.
- Confirm expected sentence and no proposed twenty merge on the known recording.
- Review safeguards before promoting as Phase 2 baseline.

LIMITATIONS
- The word-ASR boundary veto is conservative and applies only when word and segment counts match. It does not solve general forced alignment.
- Full consonant substitution improvements, word-level caregiver corrections and calibration remain for subsequent Phase 2 builds.
