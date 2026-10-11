# Improved Candidate-Word Engine

This build implements the next backlog item.

## What changed
The server now ranks known-English-word candidates using more than simple
initial/final consonant deletion.

Candidate ranking can now use:
- full phoneme edit similarity
- dropped/deleted sound evidence
- changed/substituted sound evidence
- inserted sound evidence
- acoustic and temporal evidence
- supplied context
- approved speaker word history
- approved heard-to-meaning mappings
- learned phoneme-pattern support
- existing speaker-adaptation boost

## Multiple hypotheses
The engine keeps up to eight plausible candidates. It does not rewrite the
observed speech to force a match.

## Result fields
Each candidate can now include:
- `phonemeSimilarity`
- `phonemeComparison`
- `substitutionCount`
- `deletionCount`
- `insertionCount`
- `speakerWordHistoryCount`
- `personalizedMappingCount`
- `learnedPatternSupportCount`
- `rankingEvidence`
- `reason`
- final `confidence`

The original observation remains immutable.
