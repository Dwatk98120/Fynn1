# Hearlium — Segment-by-segment caregiver review build

## New UI
Open **Record & Analyze → Review Individual Words (recommended)** after analysis.
A scrollable window shows timestamps, observed phonemes, editable suggested words, a Play clip button, and decisions for each segment.
Decisions: not_reviewed, confirmed, rejected, boundary_uncertain.

## Safeguards
- Whole-recording approval is blocked when numberReview contains more than one segment.
- Confirmed words must be a single word and cannot have an algorithm-flagged uncertain boundary.
- Original recording, observation, and phoneme predictions remain unchanged.
- Reviews are written under `%LOCALAPPDATA%\\Hearlium\\ParentPC\\segment_reviews`.
- Confirmed segments are separately exported as WAV files under `segment_reviews\\approved_clips` with a JSON manifest.
- These reviewed clips are **not automatically incorporated into the server speaker profile or model**. Future supervised training can consume them after validation.
- The original whole-recording correction controls remain for genuinely isolated single-word recordings.

## Known limitation
This first release does not provide manual boundary dragging or join/split controls. Segments marked with an ambiguous boundary cannot be confirmed in this screen; they must be re-recorded individually or addressed in a future boundary editor. It does not establish recognition accuracy.

## Build
Extract to a short directory such as `C:\\HearliumBuild`, then run `BUILD_HEARLIUM_INSTALLER.bat` on Windows. The installer itself is not precompiled.
