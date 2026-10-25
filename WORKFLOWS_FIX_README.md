# Hearlium Branch 2 - Android Workflow Build / Failure Guide

Matching releases (2026-10-25):

- **Android:** versionName `3.3.3`, versionCode `9`.
- **Parent PC:** Windows Inno Setup `0.4.8`.
- **Branch:** `hearlium-parent-pc-integration`; keep `Main` frozen.

## Build the matching APK through GitHub (no Android Studio)

1. Extract the complete source ZIP to a new folder.
2. Transfer the modified Android source, `android_no_live_verify.py`, and both
   `.github/workflows/*.yml` files into **the same relative paths on Branch 2**.
   Do not upload this whole ZIP as one GitHub repository file.
3. In `Dwatk98120/Fynn1`, open **Actions**.
4. Choose **Hearlium Android APK - Caregiver Child Names v3.3.3**.
   The alternate manual workflow is **Build Android APK - Capture Durability (manual)**.
5. Click **Run workflow**, select `hearlium-parent-pc-integration`, and start.
   Pushing the updated files to Branch 2 also triggers the named workflow.
6. Wait for a **green check**. Under the successful run's **Artifacts**, download
   `Hearlium-Android-Child-Name-Upload-v3.3.3-code9`.
7. Extract the Actions artifact ZIP to get `app-debug.apk`. The project source
   ZIP itself is not an APK or precompiled Windows installer.

## If GitHub Actions fails

Open **Actions > failed run > build > first red step**. Copy the full error
text, including any Kotlin source line and its following message. Send that
here (or upload the downloadable build logs). Also provide the workflow name,
selected branch, and failed step; the final `exit code 1` alone is not enough.

| Error / step | Check first |
| --- | --- |
| New workflow missing | Updated YAML must be committed under `.github/workflows/` on Branch 2. Check Actions is enabled and the correct branch is selected. |
| `Verify Android recording durability and source safeguards` | Verify `app/build.gradle` says `versionCode 9` and `versionName '3.3.3'`. Verify both new `student_name` and `saveStudentName` methods are present. Never bypass this check. |
| `Download official Gradle 8.9` / `Bootstrap Gradle 8.9` | An HTTP/network failure may be transient. Retry once; keep official download and pinned Gradle version. |
| Wrapper regeneration or SHA-256 failed | Do not disable the checksum. Send the exact mismatch and downloaded distribution details. |
| `Build Android debug APK` / `compileDebugKotlin` | Copy the **first** Kotlin error and any `MainActivity.kt` / `LocalSpeechRecordingStore.kt` line number. Do not use an old APK artifact. |
| `Reject outdated APKs` | Check new compiled DEX includes `saveStudentName`, `studentNameForRecording`, and `student_name`; run workflow after source changes on Branch 2. |
| No `app-debug.apk` artifact | Confirm the build job is green. Expand `Upload APK` if the Artifacts section is missing. |
| Artifact still says code 8 / 3.3.2 | Old run or wrong branch. Do not use it to test child-name uploads. |

## Warning: protect the original saved phone recordings

Install the matching **Parent PC 0.4.8 first**, then Android **3.3.3/code9**.
Try updating the existing app without clearing its data. **Do not uninstall
the app to fix an installation/signature failure.** App-private saved WAVs
may be lost when Android uninstalls an app. GitHub debug APKs created on
different runners can be signed with different keys. If Android reports
`INSTALL_FAILED_UPDATE_INCOMPATIBLE`, **stop** and request a safe data
migration/consistent-signing plan first.

## After a successful build and install

1. Android: Saved Recordings > **Analyze this saved recording**, or make a new
   recording. Type the child's name or explicitly choose Student Profile Name.
2. Press **SEND & ANALYZE ON PC**. Parent PC must confirm both the WAV SHA256
   receipt and the caregiver-entered name. A mismatched PC update blocks a
   named send rather than silently losing the name.
3. Parent PC Home: click **Recording History**. The existing searchable History
   tab opens directly; it also remains under Direct Recording.
4. Find the `Name (phone label)` row; search for the name; play the WAV.
5. The **Reference Audio Library** is *not* saved-recording search. Its search
   lists only explicitly added standard/student reference WAV clips. If it is
   empty, add a reference WAV before attempting a comparison.

Never change or delete original recordings, checksum evidence, past approvals,
or learning history. Child names here are caregiver recording labels; multiple
children on one phone still require a later **separate verified speaker-ID**
workflow before personalized learning should be approved under those IDs.
All services remain local to the Windows Parent PC (no Render endpoint).
