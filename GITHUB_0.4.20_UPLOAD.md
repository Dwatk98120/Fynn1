# Upload 0.4.20 source and build the Android APK

Use `release_0.4.20/Hearlium_0.4.20_GitHub_Ready.zip` for source only.
The separate Windows installer is `installer/output/HearliumSetup-0.4.20.exe`;
do not upload that installer as repository source.

1. Extract the ZIP into a new folder. It contains a single repository-root folder
   with `app`, `server`, `parent_pc_local`, `.github`, Gradle files and source docs.
   Verify its `SOURCE_MANIFEST_SHA256.json` before copying.
2. In your existing GitHub checkout, select `hearlium-parent-pc-integration` and
   confirm it with `git branch --show-current`. Leave Main frozen. Preserve any
   newer local work and existing `.git`, credentials, runtime data and recordings.
3. Copy the extracted folder's **contents** into that branch's repository root,
   including `.github` and `.gitignore`. Do not nest the repository folder and
   do not mirror-delete existing files. Review the diff before committing.
4. Commit and push to `hearlium-parent-pc-integration` when ready. The workflow
   **Hearlium Android APK - Caregiver Child Names v3.3.3** runs on branch pushes.
   Alternatively open Actions, select **Build Android APK - Capture Durability
   (manual)**, choose this branch and click **Run workflow**.
5. After a successful run, download artifact
   `Hearlium-Android-Child-Name-Upload-v3.3.3-code9`. Extract `app-debug.apk`.
   This is a debug APK, not a signed store release. It requires the local Parent
   PC server; analysis/models/storage/learning remain on that PC.

Android remains version 3.3.3/code9 because this release changes Parent PC and
build reliability. No APK was built locally: this machine has no Android SDK
or JDK. Remote Actions execution and artifact availability remain unverified
until the source is pushed and the workflow succeeds. This preparation performs
no remote write, commit, push, PR, merge or installation.

The source ZIP excludes `.git`, local environments, model weights, binaries,
recordings, private JSON, build caches and raw local reports. Its release proof
contains only program/source and artifact integrity information. Private adult
reference tests remain separate and do not establish pediatric clinical validity.
