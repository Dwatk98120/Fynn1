# Hearlium 0.4.19 source and build validation

This is a cumulative source-only Branch 2 handoff, including 0.4.17 Tk packaging,
0.4.18 phoneme/capture repairs and 0.4.19 protected reanalysis of corroborated legacy
aliases. Android remains 3.3.3/code9.

- Staged source suite: **463 passed, 3 skipped**, 2026-10-27, using the exact
  Python 3.12 build environment with separate temporary application data.
- Staged `android_no_live_verify.py --source`: **passed**.
- All **36 tracked program/source files** match both the current root sources and
  the exact tested frozen build stamp. See SOURCE_RELEASE_0.4.19_VERIFICATION.json.
- Frozen executable SHA-256 verified separately:
  `fa7b7191ed652b86f820144f2553cee3b8bf7b5505fba7c5f0f5f76cb65d970f`.
- Corresponding frozen archive, Tcl/Tk hidden-window and actual Evidence-tab GUI,
  server imports/self-test, Layer 2, Android retry, synthetic legacy-alias and
  native PocketSphinx alignment checks passed. Frozen native alignment produced
  13 words/45 phones for the explicitly confirmed reference; the bundled model was
  used. This establishes execution and packaging, not timing/recognition accuracy.
- Installer packaging validation confirms the frozen bundle did not change during
  compilation. Separate artifact: `installer/output/HearliumSetup-0.4.19.exe`,
  SHA-256 `8464b280e091d32b45aa29b47b260933aec992671acbec58fa7dfcddce4bfa81`.
  The installer, frozen distribution and all model weights are excluded here.
- No installation, installed-device acceptance, Git commit/push, PR, merge or
  remote workflow verification was performed by this source handoff.

Optional private-audio tests remain skipped. Tests used isolated data roots;
recordings, metadata and historical results were preserved. A separate read-only
compatibility audit of the failing legacy case preserved the existing inventory;
private audio, JSON, filenames and audit reports are not shipped in this package.

PocketSphinx forced alignment requires an explicitly caregiver-confirmed exact
reference. An AI transcript remains unverified; alignment does not independently
prove spoken words, phoneme presence, pronunciation, target-speaker identity or
learning eligibility. Separate timing JSON never replaces original WAV/metadata,
raw phoneme observations, word-recognition output or historical results.

Installed-device acceptance remains pending: reopen the older saved recording and
reanalyze it, confirm original WAV counts/hashes, retained metadata/history and the
new separate result. Check recording capture, Android retry/network interruption,
offline restart and caregiver approval/revocation using disposable test data.
No automatic installation.
