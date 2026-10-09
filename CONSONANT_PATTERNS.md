# Consonant Patterns

Added a caregiver-facing report that scans saved dialogue analysis records.

It summarizes:
- Most frequent possible missing initial consonants.
- Words with repeated possible initial-consonant omissions.
- Counts across all saved recordings.

The report uses the app's existing candidate-analysis records. Counts are descriptive pattern summaries, not diagnostic measurements. The app should require enough recordings before drawing attention to a pattern, and results should be reviewed by a caregiver/SLP when used clinically.

## Final-consonant deletion

The speech analysis also checks for a possible final-consonant deletion pattern. For a candidate target such as `cat`, an observed phoneme sequence matching `ca` is treated as evidence that the final /t/ may be absent. The server returns `possibleFinalOmission`, `missingFinal`, and `pattern: "final-consonant deletion"` when this conservative sequence check matches.

This is descriptive phoneme evidence, not a diagnosis. Caregivers/SLPs should confirm patterns across repeated observations and in context.
