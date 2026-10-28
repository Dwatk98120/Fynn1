# Android 3.3.5/code11 ? visible confirmation and main-screen build info

Read ANDROID_HOTFIX_3.3.5.md and UPLOAD_FIRST.txt. Parent PC remains 0.4.21.
The local-audio confirmation has separate full-width Remove and Keep buttons,
with scrollable explanatory text and the existing verification/approval guards.
The main screen shows the actual Android build, Gradle/AGP, UTC time and commit.
Current results: 18 JVM/Robolectric tests and 11 source contracts pass. Gradle
configuration and BuildConfig generation pass. APK build/device checks pending.
Earlier release notes below are historical.

# Hearlium 0.4.21 - Offline Pronunciation and Safe Android Cleanup

Current release: Parent PC **0.4.21**, Android **3.3.4/code10**.
Read [BUILD_0.4.21_README.txt](BUILD_0.4.21_README.txt),
[TEST_RESULTS_0.4.21.md](TEST_RESULTS_0.4.21.md) and
[GITHUB_0.4.21_UPLOAD.md](GITHUB_0.4.21_UPLOAD.md).
The complete offline NLTK resources are verified and pronunciation conversion
is exercised before readiness. Android removes local recording audio only after
fresh PC-copy verification and caregiver confirmation; metadata/audits stay.
Source suite: **517 passed, 3 skipped**; **12 real Kotlin policy/storage tests passed**.
Use only `hearlium-parent-pc-integration`; Main remains frozen. Remote APK build,
existing signing-key compatibility and installed-device acceptance remain pending.

## Historical handoff notes

# Hearlium 0.4.20 Branch 2 - Reanalysis Receipt Integrity Repair

Start with [BUILD_0.4.20_README.txt](BUILD_0.4.20_README.txt),
[GITHUB_0.4.20_UPLOAD.md](GITHUB_0.4.20_UPLOAD.md), and
[TEST_RESULTS_0.4.20.md](TEST_RESULTS_0.4.20.md).
Parent PC is 0.4.20; Android remains 3.3.3/code9. The prepared repository ZIP
contains source only; the Windows installer is a separate artifact.
Target `hearlium-parent-pc-integration`; Main remains frozen. Analysis, models,
storage and learning run on the local Windows Parent PC. Never restore Render.
The 0.4.19 notes below describe the preceding source review and release history.

2026-10-28 source review fixes are applied; see
[SOURCE_REVIEW_FIXES_20261028.md](SOURCE_REVIEW_FIXES_20261028.md).
Current checks: **488 passed, 3 skipped** after installing PocketSphinx 5.0.4
in the local `.venv`. Reanalysis rejects conflicting
same-ID declared sources and conflicting modern nested receipt identities.
The original frozen-build proof below is historical; these source changes
require a new frozen build and installed-device acceptance.

Start with [GITHUB_UPDATE_INSTRUCTIONS.md](GITHUB_UPDATE_INSTRUCTIONS.md),
[BUILD_0.4.19_README.txt](BUILD_0.4.19_README.txt) and
[TEST_RESULTS_0.4.19.md](TEST_RESULTS_0.4.19.md).
This source-only handoff replaces the previous 0.4.17 source handoff. It includes
0.4.17 Tk packaging, 0.4.18 phoneme timing/capture repairs and the 0.4.19 protected
reanalysis repair for corroborated legacy aliases. Android remains 3.3.3/code9.
Target branch: `hearlium-parent-pc-integration`. Leave Main untouched.

PocketSphinx forced alignment estimates timing for an explicitly caregiver-confirmed
reference. It does not independently verify spoken words, phoneme presence,
pronunciation accuracy or speaker identity. An AI transcript remains unverified.
Results are separate JSON under `analysis_results/phoneme_alignment_reports`;
original WAVs, metadata, raw phoneme observations, word-recognition output and
historical results are preserved. Alignment grants no learning approval.

Source regression: **463 passed, 3 skipped**. Corresponding source and frozen GUI,
Tk, native alignment, legacy-alias, server, Layer 2 and Android retry checks passed.
Installed-device acceptance remains pending. This folder contains no installer,
executable, model weights, virtual environment, recordings or private reports.
No installation, Git commit, push, PR, merge or remote verification was performed.
Historical notes below can describe superseded release or Main workflows; use the
current handoff instructions above for this update.

# First Sound Helper — Android + phoneme analysis

This package adds the audio/phoneme layer to the Android app.

Architecture:

Android microphone
  -> 16 kHz mono WAV
  -> FastAPI `/v1/analyze-audio`
  -> wav2vec2 phoneme recognizer
  -> CTC phoneme decoding
  -> pronunciation comparison
  -> candidate words
  -> child/adult confirmation

The selected model is `speech31/wav2vec2-large-english-phoneme-v2`, an Apache-2.0 English phoneme-recognition checkpoint. Its model card documents Transformers usage and reports a 0.0900 CER on its stated evaluation set. That evaluation is not an evaluation of autistic children's speech, so it must not be interpreted as clinical accuracy for this app.

For real deployment:
- host the API over HTTPS
- authenticate clients
- encrypt traffic/storage
- use explicit parental/guardian consent
- minimize or delete raw audio
- evaluate the model on appropriately consented pediatric speech
- have speech-language professionals review the candidate-generation rules
- keep human confirmation in the loop


## Rebuilt deployment package
See `GITHUB_AND_DEPLOY.md` for GitHub, Parent PC local backend, and Android API configuration.


## Visual Sentence Builder
The Android app includes a local visual sentence builder with tap-to-add word tiles, removable sentence tiles, a clear/backspace workflow, custom words, and sentence playback. It uses Personal Word Bank recordings when available and Android TTS as fallback.


## Student Communication Tools
The latest build adds local-first support features: favorite phrases, picture + voice choices, try-again practice, choice boards, quick communication needs, visual activity progress, teacher/caregiver notes, custom vocabulary, privacy/offline controls, communication modes, and the visual sentence builder. These are communication supports rather than diagnostic or therapeutic scoring.


## GitHub Setup

This repository contains the Android source for First Sound Helper.

### Keep student data out of GitHub

Do **not** commit child/student recordings, names, IDs, photos, notes, exported reports, API credentials, passwords, or signing keys. The included `.gitignore` excludes common private-data locations and audio formats.

### Automatic APK builds

GitHub Actions is configured in `.github/workflows/android-build.yml`.

On pushes and pull requests to `main`/`master`, GitHub will:
1. Check out the project.
2. Install Java and Android build tools.
3. Build a debug APK.
4. Attach the APK to the workflow as `first-sound-helper-debug-apk`.

You can also start the workflow manually from GitHub's **Actions** tab.

### API configuration

The Android build uses the `PARENT_PC_LOCAL_API_URL` Gradle property for the speech-analysis API.

For GitHub Actions, create a repository **Variable** named `PARENT_PC_LOCAL_API_URL` containing the HTTPS API address.

Do not put API keys or passwords in source code.

### Android Studio

Open this project in Android Studio. Android Studio can build the app and install it on a connected Android phone.

Gradle wrapper present in this ZIP: **no**.

If the wrapper is absent, generate/add the Gradle wrapper in Android Studio before relying on the GitHub Actions workflow.

### Basic Git commands

```bash
git init
git add .
git commit -m "Initial First Sound Helper Android project"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

### Privacy model

Communication features such as the Visual Sentence Builder, Personal Word Bank, saved phrases, picture/voice choices, and offline controls are designed to work locally. Speech analysis is a separate network-dependent function.

First Sound Helper is a communication support tool, not a diagnostic or therapeutic assessment.


## Communication Interpretation Features
The project includes context-aware candidate meanings, personal pronunciation observations, sound-pattern history, candidate comparison, context+sound matching, caregiver confirmation, communication history, picture candidates, gesture/speech notes, and an unresolved/"I'm Not Sure Yet" fallback.


## Final GitHub Setup

This repository is intended to hold the First Sound Helper Android source code.

### Before pushing
- Keep the repository private during development unless you have confirmed the project's privacy and licensing requirements.
- Never commit child/student recordings, names, IDs, photos, notes, exported reports, passwords, API keys, or signing keys.
- The included `.gitignore` excludes common private-data locations and audio files.
- Use HTTPS for the speech-analysis API.
- Keep real API credentials out of source control.

### GitHub Actions
The workflow at `.github/workflows/android-build.yml` builds a debug APK and uploads it as a workflow artifact.

Set this repository variable if the build should point at a deployed analysis API:

`PARENT_PC_LOCAL_API_URL`

Do not use GitHub repository variables for secrets. Use GitHub Actions secrets when an actual secret is required.

### Gradle wrapper
Wrapper included in this ZIP: **no**.

The project still needs the Gradle wrapper (`gradlew` plus `gradle/wrapper/*`) generated by Android Studio before the GitHub Actions build can run. Do not remove this step from the release checklist.

### Push commands

```bash
git init
git add .
git status
git commit -m "Initial First Sound Helper project"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

### GitHub Actions result
After the first successful workflow, open the GitHub repository's **Actions** tab, open the workflow run, and download the `first-sound-helper-debug-apk` artifact.

### Privacy model
The app is local-first for communication supports such as the Visual Sentence Builder, Personal Word Bank, saved phrases, picture/voice choices, custom vocabulary, and interpretation history. Network speech analysis is separate and should use HTTPS.

First Sound Helper is a communication-support application. Its speech interpretations are possibilities for communication assistance, not a diagnosis, clinical confidence score, or substitute for a qualified speech-language professional.


## Personalized Communication Learning
The app can learn confirmed student-specific meanings locally and use them as candidate suggestions later. It does not automatically decide what a student meant.


## Unified Parent PC Analysis Tools
The former trial-only Parent PC utilities have been migrated into the main
`parent_pc_local/direct_recording.py` program. The main Parent PC now includes
batch WAV analysis, an AI Dashboard, evidence inspection, recurring analytics,
raw JSON inspection, and manual API configuration/connection testing.

one Parent PC workflow to maintain.

## Android Studio Trial v3
See `ANDROID_STUDIO_READY.md`. This package includes a Gradle wrapper compatible with the project's Android Gradle Plugin 8.7.3 setup and keeps the Parent PC Local API configurable through `PARENT_PC_LOCAL_API_URL`.


## v6 observation safety boundary
This build explicitly separates immutable AI observations from revisable AI interpretations.
The five learning keys reference the original observation ID and cannot rewrite the original
observation. See `OBSERVATION_INTERPRETATION_ARCHITECTURE.md`.
