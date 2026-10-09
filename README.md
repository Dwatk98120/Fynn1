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


## Enhanced AI Trial
This package includes an optional Parent PC trial under `parent_pc_trial/` and an enhanced
server evidence layer in `server/analysis_engine.py`. The Android client remains compatible
with the Parent PC Local API and displays candidate confidence when returned by the server.

The enhanced server adds acoustic/temporal evidence and a conservative candidate-confidence
band. These are engineering signals, not clinical measurements.

## Android Studio Trial v3
See `ANDROID_STUDIO_READY.md`. This package includes a Gradle wrapper compatible with the project's Android Gradle Plugin 8.7.3 setup and keeps the Parent PC Local API configurable through `PARENT_PC_LOCAL_API_URL`.


## v6 observation safety boundary
This build explicitly separates immutable AI observations from revisable AI interpretations.
The five learning keys reference the original observation ID and cannot rewrite the original
observation. See `OBSERVATION_INTERPRETATION_ARCHITECTURE.md`.
