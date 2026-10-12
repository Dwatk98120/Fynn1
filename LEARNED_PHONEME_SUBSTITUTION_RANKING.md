# Learned Phoneme Substitution Ranking

This build implements the next backlog item: feed confirmed speaker-specific
phoneme substitutions more deeply into candidate ranking.

## Behavior
If approved learning has established a repeated pattern such as:

- expected `/k/` heard as `/t/`
- expected `/s/` heard as `/θ/`

then candidates whose expected phonemes fit that same directional pattern receive
a bounded ranking boost for that speaker.

## Important safeguards
- The original observed phoneme is never changed.
- A pattern is directional: `/k/ -> /t/` does not automatically imply `/t/ -> /k/`.
- Position-specific patterns can be tracked separately, such as
  `/k/ -> /t/ @ initial`.
- Repetition increases support using a saturating boost so learned history cannot
  overwhelm weak acoustic/phoneme evidence.
- This is designed for approved speaker-specific learning, not global assumptions.

## Candidate fields
Candidates may include:
- `learnedSubstitutionEvidence.matchedPatterns`
- `learnedSubstitutionEvidence.confirmedPatternCount`
- `learnedSubstitutionEvidence.weightedSupport`
- `learnedSubstitutionEvidence.boost`
- `rankingEvidence.learnedPatternBoost`

The Parent PC candidate display also shows when confirmed speaker patterns
contributed to a ranking.
