# Hearlium Branch 2 — Layer 1 Noise and Distortion Hotfix

Date: October 23, 2026

This full-source update builds on the tested **Layers 1–3 Evidence Quality**
hotfix. It is for the **Windows Parent PC only**. The Android app, Android
workflows, Inno Setup script, and Main branch are intentionally unchanged.
The protected original recording and all previous analysis/learning entries
must remain intact.

## Changes

1. **Possible background noise:** A conservative, non-destructive short-time
   energy screen estimates a quiet-window noise floor and compares it with
   louder frames. If the quiet-window RMS is at least 0.03 and the frame
   energy contrast is at most 14 dB, the report adds the
   `possible_background_noise` warning and deducts 25 quality-score points.
   The result appears in `recordingQuality` and the protected raw observation.
2. **Honest uncertainty:** The new `metrics.noiseAssessment` is one of
   `possible_background_noise`, `no_elevated_floor_detected`, or a
   `not_measured_*` reason when the clip is too short, quiet, or lacks
   defensible quiet/active intervals. `noiseEstimateIsValidatedSNR` is always
   `false`: frame-energy contrast is **not** a measured or calibrated
   signal-to-noise ratio. This screen cannot reliably separate a continuous
   speaker from continuous background noise and may miss transient noises.
3. **Clearer distortion warnings:** `recordingQuality.reviewRecommended` and
   `reliabilityWarning` flag heavy clipping, suspected noise, very low volume,
   mostly silence, and strong DC offset. The Parent PC review explicitly
   displays `CAREGIVER REVIEW RECOMMENDED` and tells caregivers to listen to
   the original before confirming words. Neither `usable=true` nor a quality
   score is proof that recognition is correct.
4. **Version evidence:** `qualityScreenVersion=layer1-noise-screen-v1` makes
   it possible to identify fresh results from this hotfix. Old saved analysis
   JSON is not retroactively changed.
5. **No silent decisions:** Warnings do not revoke or create any caregiver
   approval, alter the original audio, or use uncertain recognition as
   automatic training data.

## Existing manual checks completed before this build

From the user's own test recordings:

- Normal audio: quality output present (100%; no warnings).
- Mostly silent audio: 87.93% measured silence, `high_silence` detected.
- Quiet speech: RMS 0.0157, `low_volume` detected.
- Loud distorted speech: 6.24% clipped samples, `heavy_clipping` detected.

Those checks validate reported field behavior, **not recognizer accuracy**.

## Regression validation

- Full Parent PC/server suite: **178 tests passed** using a separate test
  dependency directory (pytest/requests) without changing the project
  dependency pins. Synthetic tests exercise speech-shaped clean and noisy
  clips, uniform tones and noise that must not be falsely classified,
  clipping review warnings, quiet samples, WAV checksum preservation, and
  Parent PC display wiring.
- No actual recorded student audio was used for synthetic tests.
- Full Windows PyInstaller/Inno Setup compilation and real-world noise
  sensitivity still require testing on the Parent PC.

## Building and testing on Windows

1. Keep your working Branch 2 baseline and saved user data backed up.
2. Extract the entire source ZIP into a **new clean folder**. Build and
   install using `BUILD_HEARLIUM_INSTALLER.bat` from that folder, not
   `COMPILE_INSTALLER_ONLY.bat` (which reuses an older executable).
3. Close all running Hearlium server processes before installing.
4. Run a **new analysis** of a personal test recording; do not only load an
   older saved review. Check `recordingQuality.qualityScreenVersion` for
   `layer1-noise-screen-v1` and the `metrics.noiseAssessment` field.
5. Record the same spoken phrase once in a quiet room and once near a
   moderate continuous source such as a fan, with natural pauses. Compare
   `noiseFloorRmsRatio`, `frameEnergyContrastDb`, `noiseAssessment`, and
   `reviewRecommended`. Real microphones' automatic gain control can change
   results. If no noise warning appears, do not count that as a passing
   detection test: inspect the metrics first.
6. Repeat the heavy-clipping test using **your own** existing test WAV,
   confirming the strong review warning without creating new learning.
7. Confirm previously saved analyses, approval history, and audio playback
   remain available and unchanged.

## Limits / next validation

The noise threshold is **heuristic and uncalibrated**. No clinical validity,
word error rate reduction, or phoneme accuracy improvement is claimed. Do
not use noise or clipping flags alone to infer that a child omitted a sound.
The upcoming Layer 1 benchmark should include real-life HVAC/fan noise,
television voices, transient bumps, silence, clean speech, and quiet speech,
with caregiver-verified labels and false-positive measurement. Keep the
recording's raw observations separate from AI interpretations.
