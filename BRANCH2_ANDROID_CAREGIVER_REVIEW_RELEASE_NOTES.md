# Hearlium Branch 2: Android readable results and caregiver review

This package is based on `Hearlium_Branch2_Window_Layout_Android_Readable_Results_Complete_Build.zip`.

## Changes
- Android result field shows only the Faster-Whisper suggested words when the `wordRecognition.status` is `candidate_transcription`. Otherwise it shows a plain-language unable-to-determine message.
- Technical phonemes, candidate scores, model status, IDs and diagnostics are in the **Analysis Details** dialog.
- **Confirm / Correct Interpretation** opens caregiver choices: confirm, edit, reject, unsure.
- Feedback posts to the existing Parent PC `/v1/learning/feedback` endpoint with observation and recording IDs.
- A single corrected word is *eligible* for approved learning, subject to server-side observation integrity and segmentation rules. Multiple words, rejection and unsure are recorded as unapproved feedback and never automatically trained.
- Feedback failure is visible and does not falsely claim success.

## Test before deployment
1. Build the Android APK in GitHub Actions on Branch 2. Android compilation was not run in this environment.
2. Build the Windows installer with `BUILD_HEARLIUM_INSTALLER.bat` on Windows if deploying PC source updates. Windows compilation was not run here.
3. Record and analyze on Android; verify result field contains words only.
4. Open Analysis Details; verify technical information and IDs.
5. Confirm or correct a short recording; verify Parent PC responds successfully and logs feedback.
6. Try a multiword correction; verify it is saved as feedback without automatically training a word.
7. Test rejection/unsure and network failures. Verify no false saved confirmation.
8. Test Parent PC layout at 100%, 125% and 150% scaling and confirm no clipped controls.

## Still not implemented in this release
- Segment-by-segment approval of multiword sentences (requires dedicated UI and server-side mapping).
- Full homophone ranking engine.
- Optional AAC installer checkbox and Visual C++ redistributable dependency workflow.

Keep Main frozen and preserve the current working installation as rollback.
