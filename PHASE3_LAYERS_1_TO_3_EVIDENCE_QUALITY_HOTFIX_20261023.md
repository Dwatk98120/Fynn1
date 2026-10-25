# Hearlium Branch 2 — Strengthening Layers 1–3

Date: 2026-10-23

This full-source hotfix advances **recording quality**, **acoustic/temporal
evidence**, and **phoneme uncertainty** on the Windows Parent PC. It builds on
the previous Phase 3 learning-ledger no-resurrection fix and does not change
Android source, GitHub workflows, or Inno Setup baseline 0.4.5. Main remains
frozen.

## Repairs

### Layer 1 — Recording quality

- The normal analysis API now actually computes quality diagnostics for the
  recording. Previously acoustic measures existed but the dedicated quality
  check was not wired into the standard analysis response.
- Store the quality report in both the protected observation raw evidence
  and the top-level recordingQuality response for Parent PC display,
  without modifying original audio or previous results.
- Analyze the same temporary mono downmix the phoneme model receives. For
  multichannel audio, detect channel imbalance rather than inspecting only
  the first channel.
- Screen short audio, high silence, low volume, clipping, strong DC offset,
  unsupported WAV formats, and invalid or nonfinite samples. Report sample
  rate, channel count, duration, peak, RMS, silence, clipping, and DC offset.
- The review window shows quality warnings even for otherwise usable clips.
  A quality score is a screening heuristic, **not speech-recognition accuracy**.
- Layer 1 in the 13-Layer Health Dashboard now requires real quality evidence;
  the mere presence of acoustic features does not satisfy the layer.

### Layer 2 — Acoustic and temporal evidence

- The candidate-ranking boundary signal now reads tailChange from
  temporal_features, where it is measured. Previously it incorrectly looked
  in the acoustic dictionary and silently used a constant default.
- Acoustic/temporal features remain non-destructive and **must not be used to
  infer a consonant omission without caregiver review**.

### Layer 3 — Phoneme uncertainty

- Stop inventing 0.65 confidence for phoneme tokens whose confidence is
  absent. Missing, invalid, and nonfinite confidence values are now reported
  as null, with confidence_not_measured and review-required details.
- Overall phoneme confidence is null when any token's confidence is missing.
  New missingConfidenceCount and confidenceIsValidatedAccuracy=false
  fields make limitations explicit.
- Unknown phonetic symbols remain visible and unclassified rather than
  silently being treated as valid English sound evidence.

## Regression validation

- **151 server/Parent PC unittest cases passed** after these changes,
  including **10 new synthetic layer tests**.
- Synthetic checks include normal tones, silent audio, stereo imbalance,
  clipping, short audio, DC offset, corrupt/unsupported WAV, missing/invalid
  phoneme confidence, temporal evidence, protected observation snapshots, and
  layer-health data presence.
- One existing pytest-only test module could not run in this environment
  because pytest was unavailable. It is not counted as a pass.
- **No measured improvement in word error rate, phoneme error rate, or
  consonant-error false positives is claimed.** Those require protected,
  caregiver-confirmed benchmarks on real recordings.

## Installation and testing

1. Back up the working Branch 2 source and Parent PC evidence files.
2. Extract this complete source package, merge into
   hearlium-parent-pc-integration, and build through the usual Parent PC
   Windows installer process. Do **not** merge into Main.
3. Analyze synthetic test audio (your own voice): normal speech, near-silence,
   intentionally quiet speech, and a noisy clip. Open the Parent PC review
   and verify recording-quality warnings, without approving unreliable clips.
4. Open **13-Layer Health** after analysis. Layer 1 must report that it
   produced data only when the dedicated quality screening ran.
5. Verify the original recording still plays, older analyses still appear,
   and no caregiver approval is created without explicit confirmation.
6. If a recognition or learning discrepancy appears, keep the recording and
   its observation IDs for diagnosis. Do not assume heuristic confidence is
   model accuracy or clinical evidence.

## Limits

This is a **source ZIP**, not a compiled Windows installer or APK. Automated
code regression tests have passed, but installed Windows behavior, model
accuracy, and multiple-year evidence retention require further testing.
No Silero VAD, Wav2Vec2 recognizer, or other heavy engine was added.
