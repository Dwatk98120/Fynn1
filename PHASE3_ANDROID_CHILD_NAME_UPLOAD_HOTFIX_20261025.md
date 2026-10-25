# Hearlium Branch 2 — Android Child Name on Upload (2026-10-25)

## What's new

The Android **Analyze Speech / Send & Analyze on PC** dialog has a new
**Child's name for THIS recording (optional)** field. The caregiver may type
a name or explicitly choose **Use Student Profile Name** if the local Android
profile already has a name. This is separate from speech context. A saved
phone recording can be selected and named before being sent.

The phone stores caregiver labels as new, immutable `student_label_*.json`
events next to its verified local WAV. Each event records recording ID,
speaker ID, original WAV SHA256, name, source and time. The original WAV and
original `recording_meta.json` are never altered. Corrected labels create new
events; previous label history is retained. Blank names are allowed.

For a nonempty name, Android sends `student_name` with both the verified WAV
receipt request and the analysis request. Parent PC 0.4.8 validates and
acknowledges the name. Android refuses a named transfer to an older Parent PC
that cannot echo name support, and verifies the final analysis response also
acknowledges the name and successful recording storage. It does not silently
continue an unlabelled upload.

The Windows Parent PC stores an explicit name only in that WAV's JSON metadata
as `studentName` + `studentNameSource: caregiver_on_android`. Recording History
displays `Child Name (phone label)` and searches/sorts that display label.
Its speaker ID remains exactly the captured original value. The name is **not**
a verified speaker identification or evidence of who was speaking, and is not
an approval to train. No AI recognition is treated as caregiver verification.

## Important identity protection

Android speaker IDs in the current app are per installation, not yet
independent verified identities for every child. On a phone shared by two
children, both recordings can have accurate **per-recording labels** while
sharing the same underlying speaker ID. Do **not** approve personalized
learning for multiple different children under that shared ID. A future
separate-student-profile/identity workflow is needed before shared-device
personalized learning can be considered safe. This hotfix deliberately never
renames previously imported Parent PC recordings or changes past approvals.

## Recording History shortcut and Reference Audio search

**Recording History** is a new button on the main Hearlium Parent PC window.
It opens the existing searchable/sortable History tab directly, without first
selecting Direct Recording. The tab remains available within Direct Recording.

**Reference Audio Library** is not the saved-recordings database. It searches
only number reference WAV files the caregiver has explicitly added. Its new
**Search References** button, Enter key and library selector use the current
kind and student speaker ID. A zero-results message explains that references
must be added first. A shortcut inside that window opens ordinary saved audio
History, and Choose Student WAV starts in the Parent PC recordings directory
when available. No number reference is treated as verified word accuracy.

## Install in order

1. Extract this **complete source ZIP** to a new folder on the build PC.
2. Run `BUILD_HEARLIUM_INSTALLER.bat` and install Parent PC **0.4.8** first.
3. On GitHub Branch 2 (`hearlium-parent-pc-integration`), build the Android
   APK using **Hearlium Android APK - Caregiver Child Names v3.3.3** (or the
   manual Android build workflow). Install that APK over the existing app;
   do not clear its app data, which contains saved original recordings.
4. In Android Saved Recordings, select **Analyze this saved recording**, or
   create a new recording. Enter the child's name before sending.
5. Verify Parent PC Recording History shows **`(phone label)`** next to that
   recording; search for the same child name and verify the WAV can be played.

If both phone and PC are upgraded but a name is missing, send the displayed
message and the recording ID before attempting any repeat upload. Older
pre-hotfix PC recordings stay Unassigned until explicitly relabelled in a
separate caregiver workflow; their identity is never inferred.

## Validation in this source environment

- All 7 new Android-to-Parent-PC child-name tests passed.
- Existing Android durability (5), recording search/sort (8), student library
  (11) and title/tag (12) tests passed independently.
- Six new tests cover direct Home-to-History navigation and the Reference Audio
  search/filter state, including stale search response handling.
- Android source feature gate `android_no_live_verify.py --source` passed.
- Linux does not have the Android/Windows SDK environment needed for a full
  APK or Inno Setup build. GitHub Actions must compile the APK and the Windows
  build PC must run the full regression suite and installer before release.

The ZIP also includes `WORKFLOWS_FIX_README.md` with the exact GitHub Actions
build workflow, artifact name, common failures and recovery guidance. Updating
an Android debug APK can encounter signing-key mismatches; **do not uninstall
or clear existing app data** without a plan to preserve phone recordings.

Main and all existing 13 speech-analysis layers remain frozen.
