# Expanded Phoneme Analysis

This build implements the next backlog item: stronger phoneme evidence.

## Added
- CTC-derived confidence for observed phoneme output
- overall phoneme-confidence score
- confidence band: clear / moderate / uncertain / distorted-or-unclear
- explicit uncertain or distorted sound list
- consonant vs vowel counts
- per-phoneme evidence records
- consonant features: place, manner, and voicing where known
- vowel features: height/backness or diphthong classification where known
- richer substitution evidence
- expected-vs-observed feature comparison
- feature similarity for substitutions
- confidence attached to changed and inserted observed sounds
- top-candidate phoneme comparison returned by `/v1/analyze-audio`
- Parent PC formatting for confidence and uncertain/distorted sounds
- Android helper formatting for the same data

The immutable original observation is preserved. Expanded evidence is added as annotations.
