# Actual 0.4.16 validation

2026-10-27. Full server suite: 347 passed, 3 skipped in 7.25s; exit 0.
Android source safeguard verification: PASS. pip check: no broken requirements.
Silero offline model inference: PASS.
The three skips require optional private adult references, intentionally excluded.

Read-only replay of four private adult recordings through current candidate,
prosody and diagnostic code used 49/18/20/17 full energy peaks. Original WAV,
metadata and word-recognizer outputs were verified unchanged. Candidate coverage
improves but ranking errors remain. This was not fresh model inference, clinical
validation, a learning approval or installed-device acceptance.

Frozen and installer validation results, once completed, are recorded in the
separate BUILD_0.4.16_VALIDATION.json beside the downloadable installer.

PENDING: installed Windows reanalysis/integrity acceptance, actual phone/network
retry/conflict tests, model inference in the installed build, compound-reference
UI checks, and controlled feedback/learning holdouts for layers 9-13.
The new synthetic upload-storage check is not a substitute for these device tests.
