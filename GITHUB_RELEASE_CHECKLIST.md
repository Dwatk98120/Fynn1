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
