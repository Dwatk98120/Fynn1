# Hearlium 0.4.20 validation, 2026-10-28

Parent PC release: 0.4.20. Android remains 3.3.3/code9. Main is frozen.

- Source suite: **493 passed, 3 skipped**. Full server tests plus the root
  consonant regression ran with isolated temporary application data, offline
  model flags, disabled cache/bytecode writes and JUnit output.
- The three skips require optional original private adult WAVs/metadata.
  Native PocketSphinx 5.0.4 engine/dictionary initialization now passes.
- All pinned build dependency checks and `pip check` passed. PyAV WAV decoding,
  Faster-Whisper native imports, offline Silero inference, phoneme tokenizer
  loading and the source Tk/GUI check passed.
- The .NET Bluetooth helper compiled for Windows x64 / .NET 8. Model and VC++
  prerequisite assets were copied from the supplied earlier local build folder
  and SHA-256 verified without changing the originals.
- PyInstaller built a fresh executable. Frozen checks passed: archive release
  identity/receipt guards, actual Tk GUI/Evidence tab, bundled PocketSphinx model,
  phoneme/capture hotfix, receipt-conflict rejection, server/Uvicorn protocol
  self-test, Layer 2 activity evidence and Android retry. The build was stamped
  and verified against exact executable/source SHA-256 values.
- Installer validation, SHA-256, byte size and bundle-unchanged result are in
  `installer/output/BUILD_0.4.20_VALIDATION.json`. The source package carries the
  corresponding non-private proof in SOURCE_RELEASE_0.4.20_VERIFICATION.json.
- Both APK workflows and wrapper properties agree on Gradle 8.9. Bootstrap ZIP
  and generated wrapper JAR SHA-256 checks are mandatory. YAML files and release
  scripts parsed successfully; regression tests check checksum agreement,
  current Parent PC version and source-CI dependency setup. Two packaging
  regressions also verify complete nested/empty-file hashing and reject changed
  bundles before issuing a success proof. Concurrent hashing retains the same
  full before/after SHA-256 comparison; resume verification requires a successful
  compiler log and the matching tested source/executable stamp.

Run source tests using the validated local environment:

```powershell
.\.venv\Scripts\python.exe -B -m pytest server/tests test_phase3_consonant_regression.py -q -rs -p no:cacheprovider --basetemp <new-temporary-folder>
```

Use temporary LOCALAPPDATA/APPDATA as well. This local `.venv` installs PocketSphinx
and reads the other dependencies from the user-supplied earlier build environment
through a `.pth` file. The packaged frozen executable bundles its own dependencies;
the source-only ZIP excludes both environments and all model weights.

The initial 0.4.20 archive verifier needed a correction to enumerate tuple-held
Python constants before its release/receipt-marker checks could pass. This was
a verifier issue, not a reason to bypass the check. The corrected archive check
and the separate runtime receipt-conflict check both passed.

No original recordings, metadata, approvals, historical duplicates or audit
history were modified. Validation used synthetic data. These checks establish
source/build execution and integrity; they do not establish recognition accuracy,
real-recording alignment timing accuracy or pediatric clinical validity.

No installer was installed. Installed-device acceptance remains pending: verify
saved-recording reanalysis with original inventories/hashes retained, capture,
Android retry/network interruption, offline restart, and caregiver approval and
revocation using disposable test data. GitHub remote workflow execution/APK
availability remain pending. This PC has no Android SDK/JDK; no local APK was
compiled. Use GITHUB_0.4.20_UPLOAD.md to run the prepared GitHub workflow.
