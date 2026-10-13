FIRST SOUND HELPER — RECORDING INDICATOR FIX FOR Fynn1

IMPORTANT: This ZIP contains TWO SMALL FILES. It is NOT a full replacement project.

GitHub repository: https://github.com/Dwatk98120/Fynn1
Target branch: hearlium-parent-pc-integration

STEP 1: Extract the ZIP on your computer.
STEP 2: Open your Fynn1 repository on GitHub. Switch branch selector from main to hearlium-parent-pc-integration.
STEP 3: Open the 'tools' folder (create it if needed). Choose Add file > Upload files.
        Upload ONLY apply_recording_indicator_fix.py from the extracted ZIP's tools folder.
        Commit directly to hearlium-parent-pc-integration.
STEP 4: Navigate to .github/workflows/ on the SAME branch.
        Choose Add file > Upload files. Upload ONLY build-apk-recording-fix.yml
        from the extracted ZIP's .github/workflows folder.
        Commit directly to hearlium-parent-pc-integration.
STEP 5: The new workflow should start automatically after the workflow-file commit.
        Open GitHub Actions and select 'Build APK - Recording Indicator Fix'.
        If no run appears, confirm the branch and paths; workflow_dispatch may not be available
        until a workflow is present on the repository's default branch.
STEP 6: When the workflow succeeds, download the artifact named:
        first-sound-helper-RECORDING-FIX-apk
        Do NOT download the older 'first-sound-helper-debug-apk' artifact.
STEP 7: Extract the artifact ZIP and install its app-debug.apk on your phone.
        Look for 'Not Recording · INDICATOR V2' between Record Speech and Stop.
        Tap Record Speech: it should change to a flashing red RECORDING indicator.

NOTES:
- The patch is applied temporarily within the GitHub Actions build workspace.
  It does not commit changes to the app source in the branch.
- The original app, Parent PC connection, and speech-analysis code are preserved.
- No APK build or phone behavior has yet been verified.
- If the workflow fails, share its red error log for diagnosis.
