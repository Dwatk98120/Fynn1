# Caregiver Review + Parent PC Recording History

This build expands the Parent PC direct-recording window with a review workflow and a persistent local history.

## Caregiver review
After analyzing a Parent PC recording, the reviewer can:
- confirm/correct the intended word
- approve the example for learning
- save a correction without approving it for learning
- reject the interpretation without learning from it

Approved examples are sent to `/v1/learning/feedback` and follow the existing rule:
only explicitly approved examples update the speaker profile.

## Recording history
Each `.wav` file now has a local `.json` metadata sidecar containing:
- speaker/student ID
- context
- notes
- created time
- analysis result
- observation ID
- recording ID
- best candidate
- caregiver review state
- confirmed/corrected word
- learning-feedback response when applicable

The Recording History tab supports:
- refresh
- playback
- reanalysis
- loading an old recording back into the review area
- delete recording + metadata
- review-status visibility

Original observations in the learning store remain immutable.
