# Hearlium child-speech profile and diagnostic build

## Changes
- Speaker ID starts blank; explicit confirmation required if missing or shared legacy student-1 ID.
- Speaker category selector: Child / student or Adult test / reference.
- Speaker ID and role are frozen when recording starts and saved in recording metadata.
- Adult test segments cannot be approved in the individual-word child-learning review; use Reference Audio Library for adult references.
- Optional counting 1–12 diagnostic displays the expected sequence as context, not a forced recognition result or measured accuracy.
- Existing individual-word review, transfer acknowledgment, reference comparison and analytics remain included from the prior combined source.

## Limitations and validation
- This build does NOT install or train a new child-specific acoustic model, perform biometric speaker identification, or automatically identify who is speaking.
- Existing recordings labeled student-1 are NOT migrated or relabeled. Review and separate their provenance manually before approving learning.
- Adult-versus-child comparison is exploratory through existing reference matching; no validated word-error-rate improvement is claimed.
- Windows installer and Android APK must be built and tested on the target PC/phone.
