# Hearlium Branch 2 — Layer 2 Acoustic and Timing Evidence Hotfix

Date: October 23, 2026

This cumulative **source ZIP** advances Layer 2 after the Layer 1 noise and
distortion warning hotfix. Main stays frozen. Windows Parent PC hosts all
speech processing. No Android app, Android workflow, Windows Inno Setup, or
installer builder changes are included.

## Why this change matters

The previous `finalEnergyRatio`, `finalSilenceRatio`, `peakRatio`, and
`tailChange` were taken from the end of the **file**. A valid spoken phrase
followed by 12 seconds of silence therefore appeared to end with almost no
energy. Worse, the candidate ranker rewarded `finalSilenceRatio` for a
`possibleFinalOmission` candidate. Silence after a finished sentence is not
evidence that a child omitted a consonant.

## Improvements

1. Preserve the existing recording-tail fields as original, historical
   observations. They are not deleted or silently reinterpreted.
2. Add separate **energy-activity-tail observations** using sustained 20-ms
   RMS frames and a conservative relative/absolute threshold:
   - `activityEvidenceVersion: layer2-activity-tail-v1`
   - `activityEstimationStatus`, including not-measured reasons
   - `estimatedActivityEndSeconds` (null when uncertain)
   - `trailingQuietSeconds` (null when uncertain)
   - `activityTailPeakRatio`, `activityTailEnergyRatio`
   - `activityTailChange`, `activityTailWindowMs`
   - `activityEstimateIsVerifiedSpeech: false`
3. Candidate evidence prefers the end-of-activity acoustic/temporal measurements
   when available. Appended file silence no longer lowers a non-omission
   candidate's acoustic evidence just because the recording is longer.
4. A `possibleFinalOmission` candidate receives **neutral acoustic support**
   of 0.45. The former scoring boost from trailing file silence is removed.
   This does **not** create, approve, or refute a phoneme omission.
5. The Parent PC Evidence view explains that activity is only an energy
   estimate, **not confirmed speech or proof of a missing consonant**.
6. The 13-Layer Health Dashboard marks Layer 2 as having produced data only
   when **both** acoustic and temporal fields are present in the newest
   observation. `validatedAccuracy` remains null.

## Tests

**186 full server/Parent PC regression tests passed**, including eight new
synthetic-only Layer 2 checks and all 178 tests from the preceding build.
Tests cover:

- Identical utterances with different amounts of appended silence;
  activity-relative candidate evidence stays unchanged.
- The acoustic score for a possible final omission cannot be inflated by
  changing `finalSilenceRatio` from 0 to 1.
- Empty, invalid, silent, short, and stereo audio have bounded metrics and
  explicit uncertainty; original input samples remain unchanged.
- GUI evidence labels and Layer 2 Health Dashboard requirements.

Automated tests do **not** establish word-boundary accuracy, omission recall,
consonant-error false-positive rates, or clinical suitability.

## Windows install / user validation

1. Preserve your latest working Branch 2 installer and local data backup.
2. Extract this ZIP into a new folder; run the **full**
   `BUILD_HEARLIUM_INSTALLER.bat`. `COMPILE_INSTALLER_ONLY.bat` reuses an old
   executable and is not suitable for a code hotfix.
3. Stop all Hearlium processes before installing the newly built Setup EXE.
4. Analyze a fresh personal test clip: say "Testing one two three", then
   remain quiet for 8–12 seconds before stopping. Open the NEW Raw JSON,
   not an older saved review.
5. Confirm `observation.rawEvidence.acoustic.activityEvidenceVersion` is
   `layer2-activity-tail-v1`; compare `estimatedActivityEndSeconds` against
   total duration. `trailingQuietSeconds` should account for most appended
   silence if the estimate finds sustained speech-like activity.
6. Review the Evidence panel and verify no suggestion of a **missing final
   consonant** is justified solely by appended silence.
7. Verify the original audio still plays, previous analyses remain, and no
   new caregiver approval occurs automatically.

## Limits and next phase

The energy-based activity endpoint is **not a verified speech endpoint**:
breathing, HVAC, TV, and other sounds can count as activity. It cannot resolve
individual word boundaries or phoneme deletions. Layer 1's background-noise
threshold and Layer 2's activity/temporal estimates still need protected
real-recording benchmarks and caregiver review before validation approval.
