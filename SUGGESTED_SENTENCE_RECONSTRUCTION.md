# Suggested Sentence Reconstruction

Live Session Summary playback now attempts to reconstruct a possible corrected sentence.

Example:
- Recognized: `I see the at`
- Candidate word: `cat`
- Possible playback: `I see the cat`

The app replaces the first recognized token that matches either the candidate word or the candidate word with its initial consonant removed.

This is a probabilistic communication aid. The app should present the reconstructed sentence as a suggestion rather than a definitive correction.
