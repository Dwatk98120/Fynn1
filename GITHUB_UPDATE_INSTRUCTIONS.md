# Update Branch 2 with Hearlium 0.4.19

Target branch: `hearlium-parent-pc-integration`. Leave Main untouched.
This is the current cumulative source-only handoff. It includes the 0.4.17 Tk
packaging fix, 0.4.18 phoneme/capture repairs, and the 0.4.19 legacy recording alias
repair. No remote Git operation or installation was performed.

1. Preserve your current working files and inspect `git status`. Keep credentials,
   recordings, metadata, learning data and historical results outside this source
   update. Retain any newer branch-specific work.
2. In the existing checkout run `git switch hearlium-parent-pc-integration` and
   confirm `git branch --show-current` prints that exact branch. Resolve missing
   branch setup before copying files.
3. Review CHANGED_FILES_0.4.19.txt, TEST_RESULTS_0.4.19.md and
   SOURCE_RELEASE_0.4.19_VERIFICATION.json. Compare this complete snapshot with the
   checkout before replacing files. SOURCE_MANIFEST_SHA256.json identifies every
   managed source/document file and its checksum; it excludes itself.
4. Copy this folder's CONTENTS into the Branch 2 checkout root, including `.github`
   and `.gitignore`. Do not nest the folder, replace `.git`, or mirror-delete local
   work. The superseded SOURCE_RELEASE_0.4.17_VERIFICATION.json may be archived
   separately; historical build notes remain for context.
5. Inspect `git status`, `git diff --stat` and `git diff`. Resolve conflicts and
   verify no private data, credentials or unrelated files are staged. Historical
   notes can mention Main; do not use those deployment commands for this update.
6. Set up Python 3.12 x64 with the prerequisites in BUILD_HEARLIUM_INSTALLER.bat.
   Use the exact build interpreter for checks. Tcl/Tk must be available through
   Python's own installer; do not try to install tkinter with pip. PocketSphinx is
   pinned to 5.0.4. Run `python -m pytest -q server/tests` and
   `python android_no_live_verify.py --source`; compare the results with the current
   validation document rather than assuming earlier results apply.
7. For a new Windows installer, run BUILD_HEARLIUM_INSTALLER.bat from a short path.
   It downloads prerequisites/models, runs source and frozen Tk/GUI, phoneme and
   legacy-alias gates, stamps the exact tested source/executable and creates
   `installer/output/HearliumSetup.exe` (application version 0.4.19). The separately
   prepared versioned local artifact is `installer/output/HearliumSetup-0.4.19.exe`.
   Neither binary is included here. COMPILE_INSTALLER_ONLY.bat requires a matching
   verified frozen build and cannot build this source-only snapshot by itself.
8. Android remains 3.3.3/code9. Wrapper scripts/properties are included; the wrapper
   JAR is absent. Current workflows bootstrap Gradle 8.9 and regenerate the wrapper.
   build-apk.yml is manual; build-apk-recording-fix.yml targets Branch 2 pushes and
   manual dispatch. This handoff does not establish a successful remote APK build.
9. PocketSphinx forced alignment requires an explicitly caregiver-confirmed exact
   reference (`--confirmed` for the CLI). AI-transcript-only alignment remains
   unverified and is not automatically run. Timing JSON is stored separately from
   original WAV/metadata, raw phoneme observations and word recognition. Alignment
   does not prove pronunciation or authorize learning.
10. Run the pending installed-device checks in TEST_RESULTS_0.4.19.md before
    accepting the build on devices. Install only when the user chooses to do so.
11. Commit or publish only after reviewing the staged Branch 2 source/docs.
    Publishing, PR creation, merging and Main updates are separate user actions.

Safe `.env.example` and `local.properties.example` are included. Do not commit
real configuration, keys, recordings, model caches or build artifacts. Read
THIRD_PARTY_NOTICES_POCKETSPHINX.md and THIRD_PARTY_NOTICES_CMUDICT.txt.
LICENSE_NOTICE.md still requires a project license choice before public release.
