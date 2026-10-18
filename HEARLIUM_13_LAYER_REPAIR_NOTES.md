# Hearlium 13-layer review repair — October 16, 2026

## Included changes
- **Candidate generation/classification:** final or initial **vowel** deletions are no longer mislabeled as consonant omissions; candidate scores explicitly identify themselves as heuristic ranks rather than probabilities; candidates are marked unconfirmed and ineligible for learning.
- **Word boundaries:** retains adaptive adjacent-segment join proposals, without editing raw observations.
- **Omission interpretation:** if a candidate word spans a proposed join, omission flags from its component fragments are withheld from the aggregate omission summary pending human boundary review. Individual candidate evidence is retained unchanged.
- **Review metadata:** adds `boundaryReview` with per-segment ambiguity and review status; proposed joins remain non-learning.
- **Reporting:** adds `analysisMetrics` with separate candidate coverage, ranking score, unknown segmentation confidence and unknown recognition accuracy. Human-confirmed references are required to measure accuracy.
- **Learning layers 9–13:** existing non-learning safeguard is preserved; no new autonomous training or automatic corrections were enabled.
- **Bluetooth build:** source based on the Bluetooth-fixed package with Windows SDK Contracts 10.0.19041.38.
- **Regression:** tests for adaptive joins, vowel/consonant classification, review-only boundaries, and omission suppression.

## Important scope and limitations
This is a targeted source repair affecting the identified issues across the pipeline, **not a claim that all 13 layers have been independently validated end-to-end**. A full Windows installer and Android APK were not built here. Human confirmation UI for word boundaries, audio-level acoustic model improvements, calibration, and long-term speaker learning require separate implementation and testing. `overallConfidence` retains its legacy zero value on multiword recordings for backward compatibility; consult `analysisMetrics` instead.

## Test command
From the ZIP root:
`python -m unittest discover -s server/tests -v`

## Build
Use the existing Parent PC installer scripts included in this ZIP on Windows, following their documented requirements. Rebuild the installer from this source; simply uploading the ZIP does not update an installed PC service.
