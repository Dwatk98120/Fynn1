Hearlium Android recording indicator fix
========================================
- Always-visible status between Record speech and Stop.
- Gray Not Recording when idle.
- Red pulsing RECORDING when AudioRecord successfully starts.
- ObjectAnimator used for repeating alpha pulse.
- Existing Parent PC code left unchanged.
Build the Android APK using the existing GitHub Actions workflow.
This patch has not been compiled or tested on an Android device.
