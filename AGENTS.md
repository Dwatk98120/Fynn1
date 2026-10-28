# Hearlium coding agent rules

- **Main is frozen.** Do not modify, merge, or force-push Main. Confirm the working branch is `hearlium-parent-pc-integration` before changing files.
- All analysis, models, storage, and learning run on the local Windows Parent PC; Android connects to that PC. Do not restore Render.
- Never overwrite, rename, delete, or migrate original WAV recordings, original metadata, approvals, or audit history without explicit separate approval.
- Use SHA-256 integrity checks; retain historical duplicates and provenance. New analyses are separate, versioned derived results.
- Reject recording/speaker/source/hash conflicts. Never bypass evidence-integrity checks to silence an exception.
- Preserve the 13-layer architecture. Acoustic observations and interpretation are separate; caregiver approval is required before learning.
- Existing test recordings are adult samples, not pediatric clinical validation.
- Investigate root causes, write regression tests, run tests, and report limitations before claiming a fix.
- 0.4.19 is a source snapshot; installed-device acceptance testing remains pending.

- For Android-only updates, provide the small browser-upload ZIP using `package_android_small.py` (see `ANDROID_SMALL_UPLOAD.md`); keep it at or below 100 files. Preserve the full source separately. Clearly identify any required Parent PC update; the small package does not deliver PC changes. Report actual test/build/device status.
