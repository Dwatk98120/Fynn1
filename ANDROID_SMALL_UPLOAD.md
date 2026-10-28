# Android-only browser upload option

For Android-only updates, provide the small upload ZIP as the standard download.
Keep a full source package available when requested. Parent PC or API changes
must be called out and packaged separately; this ZIP cannot deliver PC updates.

Run from this source folder with Python 3:

    python package_android_small.py --output-dir ../android-upload-output

Version name and code come from app/build.gradle. The script runs the Android
source guard, includes production Android source/resources, tests, Gradle config,
both APK workflows, this guide and the reusable packager. It excludes Parent PC
source, installers, recordings, credentials, caches and local build outputs.
New resource types require explicit packaging review. SHA-256 and archive
contents are verified. The script refuses packages above 100 files and refuses
to replace an existing ZIP. Use a fresh output folder for a repeat package.

Extract the ZIP. Select hearlium-parent-pc-integration on GitHub, then Add file >
Upload files at repository root. Drag the extracted contents, including .github,
not the enclosing folder or ZIP. Commit only to that branch. Leave existing PC
files alone. Open Actions and inspect the NEW run for the uploaded commit.
The push workflow builds the APK, runs tests and checks the resulting artifact.
A successful source package does not establish successful APK compilation or
phone acceptance. Preserve app data and signing compatibility during updates.

Future releases must update source guards and version metadata together and run
the appropriate tests before packaging. The packaging script does not run the
full test suite or claim it passed. Include actual test results with delivery.

## Current window-call correction (2026-10-28)

The dialog now declares an explicit android.view.Window receiver and calls
setBackgroundDrawable and setLayout on that receiver. Both this revision and
the preceding corrected dialog compiled in an isolated Kotlin 2.0.21 harness
against official Google API35 android.jar. Therefore the remaining reported
GitHub failure was not reproduced with the local corrected dialog; the exact
remote source/commit has not been inspected. The source guard now requires the
explicit window calls as well as the public setView(View) overload.

Current checks: public-API35 dialog compilation passed; 18 JVM/Robolectric tests
passed; 13 Python source/wiring checks passed. This is not whole-app compilation.
The full APK build and phone acceptance remain pending. Upload this entire small
package to hearlium-parent-pc-integration, commit, and open the NEW Actions run
for that commit. Rerunning an older run uses its older source commit.
