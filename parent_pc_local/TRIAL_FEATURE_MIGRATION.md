# Trial Parent PC Feature Migration

The separate `parent_pc_trial/` application has been retired.

All useful trial-only functions were moved into the main Parent PC program:
`parent_pc_local/direct_recording.py`.

## Migrated functions
- Batch Folder analysis for multiple WAV files
- AI Dashboard
- Evidence view
- Raw JSON inspection
- Recurring candidate-word analytics
- recurring changed-sound analytics
- recurring dropped-sound analytics
- manual Parent PC API URL configuration
- API connection test
- local analysis-result exports

## Why the trial section was removed
The current Parent PC already provides:
- direct microphone recording
- recording history
- caregiver approval/correction/rejection
- approved-data learning feedback
- recording-quality scoring
- expanded phoneme analysis
- One-Tap phone pairing
- Bluetooth/LAN connection support

Maintaining a second trial application would duplicate behavior and increase the chance
that the two interfaces drift apart.

## Architecture rule
The original observation remains immutable. Dashboard, evidence, analytics, and
caregiver-learning information are annotations or summaries built around that
observation and do not replace it.
