# Hearlium Branch 2 — File Integrity Phase 2 (test build)

This patch uses the previously supplied Branch 2 Storage Safety ZIP as its base.

## Change
- Recording History > Reanalyze now sends an explicit reanalysis marker to the local analysis-job endpoint.
- The server checks existing metadata recording ID, speaker ID, WAV SHA-256 and actual original WAV integrity before reusing an original.
- A reanalysis produces a separate timestamped analysis export, never another permanent WAV.
- Unknown identity, changed audio, mismatched speaker or corrupt/missing original fail closed rather than creating a new WAV.
- Existing duplicates are retained unchanged. No deletions or renames.

## Limits / verification
- This addresses explicit Recording History > Reanalyze, NOT every Parent PC or Android upload path.
- The initial Android upload retry mechanism is unchanged, including its known concurrent-request limitation.
- Existing GUI review result export behavior is retained; full end-to-end Windows validation and 13-layer regression still required.
- Target Voice Isolation is NOT included.
- Keep previous installer and backup originals. Main remains frozen. Build only Branch 2.

## Test
`python -m unittest discover -s server/tests -p test_phase3_parent_pc_reanalysis_storage.py -v`
`python -m unittest discover -s server/tests -p test_phase3_android_idempotent_storage.py -v`
Run `BUILD_HEARLIUM_INSTALLER.bat` on Windows. Do not clear AppData or the recordings folder.
