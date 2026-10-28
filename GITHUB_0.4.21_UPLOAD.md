# Upload 0.4.21 and build Android 3.3.4/code10

Use `release_0.4.21/Hearlium_0.4.21_GitHub_Ready.zip` for source only. The
separate Parent PC installer is `installer/output/HearliumSetup-0.4.21.exe`.

1. Extract the source ZIP into a new folder and verify its
   `SOURCE_MANIFEST_SHA256.json`. Preserve the original ZIP/checksum.
2. Clone/open your GitHub checkout on `hearlium-parent-pc-integration` and
   confirm that exact branch. Leave Main frozen. Preserve newer local work,
   `.git`, credentials, recordings, metadata and approval/audit history.
3. Copy the extracted repository folder's **contents** into the checkout root,
   including `.github` and `.gitignore`. Do not nest the folder or upload the
   ZIP as a single repository file. Do not mirror-delete existing files.
4. Review, commit and push when ready. The branch-push APK workflow is
   **Hearlium Android APK - Protected Local Audio v3.3.4**. The manual
   **Build Android APK - Capture Durability (manual)** workflow also works:
   select Branch 2 before choosing Run workflow.
5. The workflow verifies Gradle 8.9 SHA-256 values, runs `testDebugUnitTest`
   and `assembleDebug`, and checks the compiled APK for the new storage,
   caregiver-confirmation and PC-copy verification code. Download artifact
   `Hearlium-Android-Protected-Local-Audio-v3.3.4-code10` after success.

Use Parent PC 0.4.21 with the new APK. Older PCs cannot provide the fresh stored-
copy verification endpoint, so local audio cleanup remains blocked. The older
transport receipt explicitly has `stored: false` and is not a deletion permit.

The APK is a debug build. Updating an existing installation requires a matching
signing key; fresh GitHub runners may generate a different debug key. Do not
uninstall the existing app or clear its data to force an update: keep original
captures until a compatible update and verified PC copies are available.
No signing keys or credentials are included in this source package.

After installation, use disposable test recordings to check upload/analysis,
matching stored-copy confirmation, caregiver cancellation, offline/disconnected
PC, hash/source/identity conflicts, single/bulk removal, retained history and
PC original counts/hashes. Never use production originals to test deletion.
Existing adult samples do not establish pediatric clinical validity.

No remote push, workflow execution, APK signing compatibility or physical-device
acceptance is claimed by local source preparation. The local JVM policy tests
are separate from compiling/running the entire Android app on a device.
