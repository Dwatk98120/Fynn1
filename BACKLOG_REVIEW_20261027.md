# Hearlium backlog review — 2026-10-27

This review separates demonstrated behavior from old unchecked templates.
Parent PC and Android have separate version numbers.

## Next Android hotfix — requested 2026-10-28

- [x] Implement build information and Gradle information directly on the Android
  app's main screen, without opening a settings or diagnostics menu.
  - Display the installed app's version name and version code, build type
    (debug/release), build date/time with timezone, and commit identifier when
    available. Clearly label unavailable fields rather than guessing values.
  - Display the Gradle version actually used to produce the APK and the Android
    Gradle Plugin version. Capture these at build time; do not display only
    expected versions from documentation or a hard-coded release label.
  - Keep the information compact, readable and clearly identified as Android
    build information so it cannot be confused with the Parent PC version.
  - Verify the installed APK's main-screen values against the successful build
    log and artifact metadata; check readability on a physical phone.

Implemented in Android 3.3.5/code11 source and covered by formatter/wiring tests.
Physical-device verification remains pending. The older 0.4.21 source ZIP is unchanged. The older status notes below are
historical and do not supersede the current release validation documents.

## Confirmed

- Parent PC 0.4.14 is running, per the user's report. Installer source and UI regression checks identify 0.4.14 as Saved Recording Reanalysis Repair.
- Android source remains version 3.3.3 / code 9; Parent PC startup does not verify Android installation or behavior.
- 22 targeted regression tests passed: saved-recording reanalysis route, Android retry, reanalysis job guard, original storage preservation, and duplicate-WAV write barrier. These are source tests, not installed end-to-end tests.
- Gradle wrapper scripts and properties exist. The wrapper JAR is absent.
- Current APK workflows bootstrap Gradle and regenerate the wrapper; the missing local JAR alone does not establish a CI failure.
- `.gitignore` includes common student-data, recording and credential exclusions. This does not establish that the repository or its history is clean.

## Current validation backlog

0.4.15 adds automatic before/after WAV integrity reports for protected
reanalysis, with review blocked on a difference or check error. Source suite:
337 passed, 3 skipped. Frozen self-test and Layer 2 verification passed.
The installed end-to-end items below remain pending.

0.4.16 adds speech-review repairs from the four private recording reviews and
a repeatable isolated Android retry/conflict storage check. Full server suite:
347 passed, 3 skipped. Next backlog item now has synthetic verification support;
actual phone/network validation remains pending. See BUILD_0.4.16_README.txt.

- [ ] On installed 0.4.14, analyze an existing disposable saved recording and use History reanalysis; compare original WAV count and SHA-256 before/after. Confirm new analysis results without replacing original evidence.
- [ ] Retry an Android upload of the same recording; verify original WAV reuse and separate analysis results. Verify conflicting identity/audio is rejected.
- [ ] Verify Android 3.3.3 installation, microphone permission, durable capture, failed-upload recovery, optional child-name upload, pairing and results display on the actual phone.
- [ ] Verify offline communication, pictures, choices, sentence building and recorded-word playback on pilot devices.
- [ ] Verify installed speech-model inference, offline restart and required runtime behavior; startup alone does not establish analysis success.
- [ ] Verify caregiver approval, revocation and Learning History reconciliation without reviving superseded approvals.
- [ ] Verify uninstall/reinstall preserves intended recording and learning data using disposable test data.

## Release and documentation backlog

0.4.18 implementation follow-up: new Parent PC captures now record their
identity/checksum before first analysis and use protected original reuse.
Adds per-token CTC timing/confidence, review-only boundary alternatives and
many-to-many timing groups, the missing "want" vocabulary entry, and opt-in
offline confirmed-reference PocketSphinx alignment. Source suite: 431 passed,
3 skipped. Read-only replay preserved all 274 existing WAVs and the original
test metadata; "want" ranked first in all three occurrences. Reference alignment
proposed 13 words/45 phones. These are implementation/replay checks; the
unchecked installed-device items above remain pending, as does manually
annotated phoneme-boundary accuracy evaluation. See BUILD_0.4.18_README.txt.

- [ ] Update stale README and repository status: old product/architecture details, missing-wrapper wording, workflow filename and trigger claims. Current `build-apk.yml` is manually triggered and regenerates the wrapper.
- [ ] Complete or document the local Gradle wrapper setup; its scripts currently reference an absent JAR.
- [ ] Select/add a project license before public release; `LICENSE_NOTICE.md` is still a placeholder instruction.
- [ ] Verify successful remote APK workflows, downloadable artifacts, repository settings, variables and production signing when preparing a release.
- [ ] Audit tracked files and repository history for student data and secrets; review remote secrets/variables. Git is unavailable on PATH here and no local `.git` directory was visible, so commit/history state was not verified.
- [ ] Complete caregiver setup and review storage/network behavior, consent, privacy, accessibility and retention for pilot use.
- [ ] Verify transport/authentication against the intended deployment; old HTTPS checklist entries do not establish the current Parent PC local configuration.

## Scope limits

No new feature backlog was established by this review. Older notes mentioning Silero as future work are superseded by later integration notes. Older stronger-phoneme, candidate-engine and learned-substitution notes describe implemented work. Running 0.4.14 establishes user-reported startup, not completion of the validation items above.

- [ ] Audit other system-button dialogs for the same large-font/OEM clipping seen in the 3.3.4 removal confirmation. The dedicated 3.3.5 removal dialog has simulated layout coverage; other dialogs are unchanged.
