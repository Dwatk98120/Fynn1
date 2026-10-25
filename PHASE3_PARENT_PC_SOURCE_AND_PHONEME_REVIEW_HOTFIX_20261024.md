# Hearlium Branch 2 — Parent PC Source and Layer 2/3 Review Hotfix

24 October 2026. Complete cumulative Parent PC Windows **installer source** ZIP,
based on the verified Layer 2/3 timing build. Main remains frozen. Android
app sources and GitHub workflows are unchanged.

## Evidence for the repair

David recorded the adult reference phrase **"Test one two three"** directly
into the Parent PC, followed by household ambient sound and distant
conversations. The 24.284-second original WAV's SHA-256 exactly matched
the saved JSON `recordingStorage.sha256`:

`15489f121690190c5e1a2fe320c7dba38d622d85cb86d7f5fd2fd014bf86048b`

Faster-Whisper's unverified word hypothesis ended at 2.27s; phoneme CTC
output continued to 24.284s. The earlier Layer 2/3 guard identified 66 late
phoneme segments, withholding all 66 automatic word guesses while retaining
all 324 raw phoneme symbols as evidence. The recognizers were **not** in
agreement; neither the unverified timestamps nor the audio energy alone can
establish speech-vs-ambient identity.

The JSON incorrectly marked this PC-origin recording as `source: android`.
This originated in the shared server-side storage helper, not in the WAV.

## Repair

1. The Parent PC-specific `/v1/analysis-jobs` queue carries a validated
   recording source through analysis to storage. New PC recordings are
   `parent_pc`, while reanalyzing a saved Android recording **on the PC**
   retains `android` provenance. The unchanged Android `/v1/analyze-audio`
   route defaults to `android`.
   Only the two known source values are accepted; unexpected values fail
   rather than generating misleading evidence metadata.
2. The server's separately saved analysis WAV, metadata JSON and result JSON
   now agree on the audio source and WAV SHA-256. PC-origin server copies
   use `parent_pc_api_` rather than `android_` filenames. The Parent PC's
   original WAV is still independently saved first, unchanged.
3. New Parent PC microphone metadata explicitly includes `source=parent_pc`.
4. The main recording result and AI Dashboard lead with a visible, human-
   review-required timing explanation when late CTC segments or a stretched
   word hypothesis is present. It reports the word/CTC end timestamps,
   flagged/withheld counts, and uncertainty about distant voices and noise.
5. The main screen shows a short labeled preview of extremely long raw CTC
   output when the timing warning is active. **Full raw evidence remains
   untouched** in the Evidence and Raw JSON tabs and stored analysis.
6. Technical audio quality is explicitly distinguished from validated word
   recognition, correct phonemes, or speaker separation.
7. Frozen-EXE and installer-integrity checks require the new source files.
   `COMPILE_INSTALLER_ONLY.bat` cannot silently reuse a previous build stamp.
8. The queued-job idempotency key includes recording source so a PC analysis
   cannot silently reuse an earlier job with a different origin declaration.

## Safety and migration

- Existing original recordings, older `android_` server copies, existing
  analysis exports and learning/audit history are **never migrated, renamed,
  deleted or silently rewritten** by this hotfix.
- This package neither automatically accepts a caregiver correction nor
  trains on an unconfirmed suggestion. The previous conservative timing hold
  remains unchanged.
- Parent PC server recording copies are still separate files in Recording
  History; no history deduplication or deletion behavior was changed.
- Withheld phonemes are **not classified as ambient noise**. Distant voices,
  genuine speech and other sounds remain unresolved without human review.
- A legacy analysis result might still have `recordingStorage.source=android`
  even when its original was captured on the PC. New analyses correct the
  marker; old evidence is retained unchanged.

## Verification

- Full Python regression suite: run `python -m pytest -q server/tests` after
  installing test dependencies. No models or internet required for the tests.
- Optional **read-only adult WAV** checksum test when the local file is present:

  ```bat
  set HEARLIUM_SOURCE_REVIEW_REFERENCE=C:\your\private\test_audio.wav
  py -3.12 -m pytest -q server\tests\test_phase3_parent_pc_source_review_hotfix.py
  ```

- On Windows, extract to a fresh folder and run
  `BUILD_HEARLIUM_INSTALLER.bat` first. It installs build dependencies,
  runs the full regression suite, bundles offline recognizers, verifies the
  new frozen executable and builds the Inno Setup installer.
- After installation, review a **non-approved adult test** from Recording
  History: verify the warning appears before raw phonemes, save/export its
  analysis, compare the WAV SHA-256, and check
  `analysisResult.recordingStorage.source=parent_pc`.
- Recheck one Android-origin submission in a later dedicated mobile test;
  its API contract and source files were not changed here.

This Linux environment cannot compile or exercise the Windows Inno Setup
installer. Passing Python tests and ZIP integrity checks do not substitute
for David's Windows installer/recording test. No child voice files or
caregiver recordings are included in the distribution.
