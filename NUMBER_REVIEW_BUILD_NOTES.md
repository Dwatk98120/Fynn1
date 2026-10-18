# Number Review and Reference Library Repair

- Added `numberReview` to `/v1/analyze-audio`, preserving all existing fields.
- Reports actual reference counts for the standard library and the current student ID, including counts per number.
- Attempts acoustic comparisons for plausible individual number segments only when corresponding WAVs exist. Scores are exploratory DTW distances, never recognition accuracy.
- Recording window displays timestamped phoneme segments, candidate words, proposed boundary joins, and library status.
- Empty libraries show instructions to open **Reference Audio Library** in the main Parent PC window and upload individual WAVs. Existing reference files are not bundled or changed.
- No changes to Bluetooth, Android, installer scripts, or human approval logic. Observations remain immutable.
- On Windows, run `BUILD_HEARLIUM_INSTALLER.bat` from the extracted folder. This ZIP is installer source, not a compiled EXE.
