# Hearlium Branch 2 — Word-ASR / Silero and Speech-Window Quality Hotfix

**Date:** October 25, 2026. Cumulative **Windows Parent PC installer source**, not a
precompiled `.exe`. Keep Main frozen. No Android source changes. All models,
speech evidence, local APIs, and learning remain on the Windows Parent PC.

## Scope

- **`wordAsrActivityReview`:** Match each timestamped Faster-Whisper *segment*
  to independent Silero candidate-speech intervals. Flag entirely unsupported
  snippets and suspicious segments that span long quiet gaps. Show uncertainty
  and original timestamps; never delete or silently rewrite the ASR transcript.
  Whole-sentence segments are not verified word-level timestamps. Silero may
  miss quiet/atypical speech or detect singing/television speakers.
- **`speechWindowQualityReview`:** Measure RMS, peak, sample-threshold ratio,
  and clipping in Silero candidate activity windows. Report whether whole-
  session high-silence scoring may reflect intentional pauses; do **not**
  downgrade genuine low-volume or clipping warnings. Existing
  `recordingQuality` and immutable acoustic observations remain unchanged.
  Windows are not identified as the child's actual speech or validated SNR.
- **`recognizerDisagreementReview`:** Summarize word-ASR/VAD timing warnings,
  phoneme/VAD holds, stretched ASR boundaries, and low independent model
  agreement in the Parent PC Dashboard and Evidence view. No automatic
  decisions are based on these hypotheses.
- **Windows packaging:** Add all three modules to the PyInstaller hidden
  imports so the frozen Parent PC executable can load them.

## Replayed against David's unapproved adult test audio

All checks used the existing WAVs and saved JSON. **No private audio or
child-specific recordings are included in this ZIP.**

| Test | ASR segments completely outside Silero | Signal RMS inside candidate windows | Session RMS | Intentional-pause bias review |
| --- | --- | ---: | ---: | --- |
| 50% mic | One: unverified `You` at 22.9–24.9 sec | 0.0065 | 0.0027 | Yes |
| 70% mic | None | 0.0068 | 0.0025 | Yes |
| 80% mic, quieter background | None | 0.0146 | 0.0056 | Yes |
| 80% mic, louder TV/music | None | 0.0130 | 0.0053 | Yes |

The first long Faster-Whisper sentence spans both utterances and a long gap;
it receives a **stretched segment** timing warning on all four files. This
does not make its words false. The extra 50% `You` is flagged as requiring
listening, not labeled a hallucination or automatically removed. The original
word recognition, CTC evidence and recording SHA-256 are not modified.

**Interpretation:** The historical whole-session quality score can be biased
by the deliberately long gaps, but some speech windows still have low RMS.
Do not convert `poor` into `good` automatically. Both signal strength and
background-source confusion need ongoing protected benchmarks with annotated
audio. These metrics are not clinical or speaker-specific accuracy claims.

## Build and acceptance

1. Keep your last working installer and original Parent PC recording database.
2. Extract the ZIP into a **new** short Windows directory, e.g. `C:\H25B`.
3. Close Hearlium and run `BUILD_HEARLIUM_INSTALLER.bat`. Do **not** use the
   compile-only shortcut, which can reuse an outdated `.exe`.
4. Require the dependency, model verification, full regression, frozen
   server self-test, and Inno Setup stages to pass. A Windows compiled
   executable has **not** been built or tested in this Linux environment.
5. Install `installer\output\HearliumSetup.exe` only after success.
6. Reanalyze **unapproved adult** 50/70/80% recordings (plus noisy 80%) and
   export their new JSON. Inspect the three new fields in `analysisResult`
   or at the root depending on the export, and verify the original WAV hashes.
7. Specifically confirm the 50% trailing `You` receives a timing-review
   warning but the text and history are preserved. No learning without an
   explicit caregiver-approved reference.

## Validation limits

- The three new Python modules were tested in isolated model-free regressions
  and replayed using saved 50/70/80% adult test WAVs. A full Windows
  installer build/benchmark is still required before treating this as an
  approved production baseline.
- Silero's absence of activity is not proof a child did not speak. No speech
  source separator, noise reduction, or new recognizer is added here.
- Existing 13-layer architecture, immutable observations, approval history,
  Android recording/upload flow and working Main baseline remain protected.
