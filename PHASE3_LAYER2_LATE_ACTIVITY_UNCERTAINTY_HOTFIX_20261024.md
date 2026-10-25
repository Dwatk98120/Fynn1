# Hearlium Branch 2 — Layer 2 Late Sound Activity & Uncertainty (24 Oct 2026)

## Ground truth available

Two user-submitted **JSON analysis exports**, not the original WAVs, showed:

- Adult reference recording A: 13.156 seconds, 80.18% nominal silence, yet
  Layer 2 v1 placed the last energy activity at 12.34 seconds and assigned only
  0.816 seconds trailing quiet. Prosodic peaks were near 1.6–3.4 seconds.
- Adult test recording B: 16.25 seconds, 87.93% nominal silence, Layer 2 v1
  placed activity end at 4.40 seconds with 11.85 seconds trailing quiet.

Both exports proved the new executable ran Layer 2 v1. This is **not** evidence
that the original audio data was faulty. Without the WAVs, we cannot say what
the later sound in A was or prove that v2 fixes its exact endpoint.

## Change (Layer 2 v2)

The v1 algorithm used the last pair of 20-ms frames above an energy threshold
anywhere in the WAV, including an incidental noise during the silence period.
Layer 2 v2:

1. Groups active frames into separated energy islands, bridging only short
   normal within-phrase gaps.
2. Uses the largest sustained-energy island as the **tentative** activity
   boundary when later islands are clearly weaker.
3. Reports `weakLateActivityIslandCount`, `lastDetectedEnergyActivitySeconds`,
   and `activityIslandCount` so late sounds are never hidden from raw evidence.
4. Reports `ambiguous_separated_activity_islands`, leaves
   `estimatedActivityEndSeconds` and `trailingQuietSeconds` null, and sets
   `ambiguousActivityIslandCount` when significant separated sound could be
   additional speech. A null means **unknown**, not no speech.
5. Preserves the unmodified raw audio, original file-relative tail evidence,
   immutable raw observation policy, and caregiver-only learning approvals.
6. Updates the Parent PC Evidence panel and the frozen-executable version check
   to require `activityEvidenceVersion: layer2-activity-tail-v2`.

This is intentionally cautious: acoustic energy is **not** a true voice
activity detector, does not recognize words or phonemes, and cannot reliably
distinguish quiet speech, a fan, a cough, or radio speech. Do not turn these
heuristics into clinical findings or auto-approved learning.

## Validation procedure

1. Build and install with `BUILD_HEARLIUM_INSTALLER.bat`, never the Inno-only
   script against an older `dist` EXE. The frozen EXE has a v2 self-test.
2. Reanalyze the existing adult reference recordings A and B, keeping previous
   analysis history intact. Export the *new* Raw JSON each time.
3. Check `activityEvidenceVersion` = `layer2-activity-tail-v2` and inspect
   `activityEstimationStatus`, `estimatedActivityEndSeconds`,
   `trailingQuietSeconds`, `lastDetectedEnergyActivitySeconds`, and island
   counts. If status is ambiguous, regard the time as not measured.
4. Confirm the original WAV still plays and its SHA-256 remains unchanged.
5. Test short late tapping/noise, two clearly separated spoken phrases, and
   a brief word-internal pause with your own voice; compare against the
   human-known phrase boundaries before approving the layer.

Regression tests use synthetic generated sound only and cannot certify the
real-world ability to locate speech boundaries. Android sources and workflows
are unchanged; the Parent PC remains local/offline and Main remains frozen.
