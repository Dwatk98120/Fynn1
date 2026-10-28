# 0.4.21 current checklist

Use GITHUB_0.4.21_UPLOAD.md and TEST_RESULTS_0.4.21.md. Parent PC 0.4.21, Android 3.3.4/code10.
517 source tests and 5 real Kotlin policy tests pass; 3 private-audio checks are skipped.
Main frozen. APK compilation/signing compatibility and device acceptance remain pending.

## Historical checklist

# Hearlium 0.4.20 handoff status

Current target is `hearlium-parent-pc-integration`; leave Main untouched.
Source: 493 passed, 3 optional private-audio skips. See TEST_RESULTS_0.4.20.md
and SOURCE_RELEASE_0.4.20_VERIFICATION.json for current build validation.
Installed-device checks and remote GitHub/Android builds remain pending.
The wrapper scripts/properties are present; the wrapper JAR is absent and current
workflows regenerate it. Read GITHUB_UPDATE_INSTRUCTIONS.md before using this list.

# GitHub Release Checklist

## Repository
- [ ] Repository name and description are appropriate.
- [ ] Repository visibility is intentional.
- [ ] `.gitignore` is committed.
- [ ] README is current.
- [ ] A license has been selected before public release.

## Android build
- [ ] Android Studio opens the project.
- [ ] Gradle sync succeeds.
- [ ] Debug APK builds.
- [ ] App installs on a test Android phone.
- [ ] Microphone permission works.
- [ ] Offline communication features work without the API.
- [ ] Speech-analysis API works over HTTPS when enabled.
- [ ] Release APK is signed with a protected keystore.

## GitHub Actions
- [ ] Gradle wrapper is committed.
- [ ] `PARENT_PC_LOCAL_API_URL` repository variable is configured if needed.
- [ ] Actions workflow succeeds.
- [ ] APK artifact can be downloaded.

## Privacy
- [ ] No student data is in Git.
- [ ] No child recordings are in Git.
- [ ] No credentials or signing keys are in Git.
- [ ] Production privacy/consent procedures have been reviewed.
- [ ] Repository history has been checked for accidentally committed secrets.

## Current project status
Gradle wrapper present in this ZIP: **NO — generate it in Android Studio before relying on GitHub Actions**.
