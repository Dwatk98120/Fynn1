# Hearlium Branch 2 — Phase 3 Android Capture Durability Hotfix

Date: October 23, 2026

## Priority addressed

The ordinary Android Record Speech / Stop flow previously kept raw PCM only
in a volatile in-memory buffer. The Saved Recordings screen existed, but
completed ordinary recordings were not automatically written there. If Android
closed or the caregiver had to reconnect to the Parent PC before uploading,
the captured speech could be lost. Also, an earlier analysis/review selection
was not cleared when another recording started.

## Changes

1. After a normal **Stop**, finish the microphone reader thread and write the
   original WAV to the Android app-private `dialogue_history` folder *before*
   any network request. A new `recording_meta.json` records its recording ID,
   original session and speaker IDs, byte size, capture time and SHA-256.
2. Write files using a temporary file, flush/sync, then rename on the same
   filesystem. Existing audio files are never overwritten.
3. On relaunch, offer the most recent checksum-verified recording for retry.
   Never silently substitute an older recording when the newest is corrupt.
4. The **Saved Recordings** screen now offers an **Analyze this saved
   recording** action. It selects the verified original and presents the
   context/Send & Analyze confirmation; it never sends without caregiver action.
5. Upload the verified saved WAV with its original IDs. No unpersisted PCM
   audio is sent. The receipt SHA-256/byte count handshake remains intact.
6. Save each successful analysis as a separately named JSON result next to
   the original recording. Re-analysis never overwrites the original audio
   or a previous analysis. Display the latest analysis in Saved Recordings.
7. Clear previous observation/analysis/caregiver review state at the start of
   a new capture and when a different saved recording is selected. Clear an
   active deleted capture so it cannot be uploaded afterward. If saving a
   previous recording failed, prevent a new capture from overwriting its
   remaining in-memory audio until the save can be retried successfully.
8. The existing `android:allowBackup="false"` remains: Android does not
   automatically place the locally saved audio in cloud backup.

## Build and safeguards

- Complete Branch 2 source ZIP, **not** a prebuilt APK or Windows EXE.
- Android version **3.3.2**, `versionCode 8`, so the correct build can be
  distinguished from stale APKs reporting 3.2, 3.3 or 3.3.1.
- GitHub Actions validates the source before building and inspects the
  generated DEX code before uploading an APK artifact.
- The earlier Live Recording removal source is carried forward but is
  **not the main focus**. Per the caregiver's request, the current GitHub build
  gate does not fail solely because old Live Speech UI references remain.
  It does fail when the compiled APK lacks the new durable-recording code.
  Regular Record Speech and Stop remain functional targets.
- Parent PC Windows Inno Setup remains **0.4.5**; all analysis, learning
  and API services stay on the local Windows Parent PC.
- Main and the last working Windows installer baseline are not modified.

## Tests and limitations

- New Python structural regression guards exercise evidence-saving paths,
  checksum/integrity requirements, selection reset and build-version gating.
- Existing backend regression suite should be re-run when dependencies are
  installed. This update does not change backend production code.
- GitHub must compile the Kotlin app, and Android must be tested on a real
  device. Check Record Speech → Stop → force-close/reopen → Saved Recordings
  → Analyze saved recording → Parent PC receipt and analysis → Play/View.
- An interrupted recording **before Stop** is not guaranteed recoverable.
  Clearing app data or uninstalling the app can delete app-private originals;
  always back up important recordings to the protected Parent PC.
- Previously saved sessions without `recording_meta.json` remain available
  for legacy playback/viewing but are not automatically selected for verified
  retry. This protects identity and evidence integrity.

## GitHub

Extract the source ZIP and update repository files on the
`hearlium-parent-pc-integration` branch only. Run
**Hearlium Android APK - Saved Recording Safety v3.3.2** and download
`Hearlium-Android-Capture-Durability-v3.3.2-code8`.
Do not upload the ZIP as a single file expecting GitHub to extract it.
