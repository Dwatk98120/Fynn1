BRANCH 2 AUTOMATIC APK BUILD - OCT 14 2026

Target: hearlium-parent-pc-integration ONLY. Do not upload to main.

1. Extract this ZIP to a folder on your PC.
2. In GitHub, select branch hearlium-parent-pc-integration.
3. Upload the extracted project files, preserving folders INCLUDING .github/workflows.
4. Commit to Branch 2. Any push to Branch 2 triggers Build Android APK - Branch 2 Auto.
5. Go to Actions, open the new run, and download artifact first-sound-helper-branch2-apk.

IMPORTANT: GitHub's web uploader may not overwrite existing files reliably, and may not preserve folder structure if uploading individual files. Verify that the file .github/workflows/build-apk-recording-fix.yml on Branch 2 has changed after your commit. If the upload interface cannot overwrite it, edit that workflow directly on Branch 2 in GitHub.

No manual Run workflow button is needed. The automatic push trigger has no paths filter.
The Android source is based on the previously supplied Branch 2 recording workflow ZIP. It has not been compiled or device-tested here.
Main is not changed by this ZIP.
