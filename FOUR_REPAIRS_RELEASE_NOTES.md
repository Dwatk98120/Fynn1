# Hearlium four-repair source build

Based on the Bluetooth UnicodeEncoding compilation-fix ZIP (preserved Windows .NET 8 Bluetooth helper and Inno Setup installer builder).

1. Learning safeguard: approved learning from multiword recordings requires `segment_index`; ambiguous segment boundaries are rejected; one-word-only approvals; approved segments map their own observed phonemes to the caregiver-confirmed word. Old clients can still submit unapproved feedback, but approving an entire multiword recording returns HTTP 400 instead of silently corrupting learning.
2. Word-boundary hypotheses: `wordSequenceReview` provides up to three bounded, review-only candidate sequences from original CTC segments and plausible adjacent joins. Original CTC observations are never overwritten, and no expected 1-12 answer is imposed.
3. Reference integration: `referenceAudioComparisons` optionally compares isolated number-candidate segment clips against previously stored standard and speaker-specific reference WAVs. No reference -> no comparisons. Distances are exploratory and never trigger learning or count as accuracy. Existing reference endpoints and GUI remain.
4. Evaluation: only human-approved examples with a comparable candidate prediction increment evaluated/correct; otherwise accuracy remains unknown. Segment-level approved examples can be evaluated against the segment candidate.

## Compatibility and limitations

- Existing Parent PC and Android clients are preserved. Existing learning endpoint accepts an optional `segment_index` integer; clients that do not send it cannot approve multiword recordings (intentional safety behavior). Segment-level approval UI is not added in this release; API clients may use the optional field. Do not use the legacy approval control for multiword recordings.
- `wordSequenceReview` is a ranking heuristic, not verified recognition. Reference DTW is not calibrated speech accuracy and may misrank words. Acoustic/phoneme recognition model weights are unchanged.
- Existing previously approved learning examples are not automatically rewritten or cleaned; review existing stored profiles if multiword examples were approved before this build.
- Validation: 20 local Python unit/regression tests passed, Python compilation passed. Windows Inno Setup and .NET Bluetooth compilation cannot be run in this Linux environment. Build on Windows using `BUILD_HEARLIUM_INSTALLER.bat`.
