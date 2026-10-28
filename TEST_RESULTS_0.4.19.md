# Hearlium 0.4.19 source and build validation

## Source review update, 2026-10-28

Latest validation after adding PocketSphinx: **488 passed, 3 skipped** in 11.57s.
The Windows x64 CPython 3.12 PocketSphinx 5.0.4 wheel is installed in this folder's
ignored `.venv`. The bundled native engine/dictionary initialization test now
passes, including model-file SHA-256 provenance. `python -m pip check` reports
no broken requirements. Remaining skips are only the three private-adult-audio
checks. Run with `.venv/Scripts/python.exe`; this local test environment uses
`hearlium_build_environment.pth` to read the other installed dependencies from
the user-supplied 0.4.12 build environment, which was not modified. This is a
local test setup, not a portable installer. Frozen rebuild/device acceptance
and real-recording alignment validation remain pending.

The following records the earlier run before PocketSphinx was added:

Current source: **487 passed, 4 skipped**, using the Python 3.12 build interpreter
in the user-supplied 0.4.12 folder, with temporary LOCALAPPDATA/APPDATA, offline
model flags, disabled bytecode/cache writes, and an isolated pytest base folder.
Command: `python -B -m pytest server/tests test_phase3_consonant_regression.py -q -p no:cacheprovider --basetemp <temporary-folder>`.
Android `android_no_live_verify.py --source` and the extended
`installer/verify_legacy_alias_build.py` synthetic source check passed.

The 21 added cases cover modern nested identity/source conflicts, cross-copy
declared-source conflicts, invalid declared sources, and valid reuse. With the
new report-version assertion, 20 checks failed before the fixes and now pass.
Conflict tests compare every fixture file before/after rejection, including
checking that no derived analysis was written. Three existing assertions now
expect the more precise source-conflict error instead of legacy-unverified.

Three skipped checks require optional private adult audio; the fourth requires
PocketSphinx, absent from this interpreter. No pediatric clinical validation,
native PocketSphinx execution, frozen rebuild, installer or device acceptance
is claimed for the revised source. All validation below describes the original
2026-10-27 release, not the current modified source. See
SOURCE_REVIEW_FIXES_20261028.md for integrity/provenance details.

## Historical release validation, 2026-10-27

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
