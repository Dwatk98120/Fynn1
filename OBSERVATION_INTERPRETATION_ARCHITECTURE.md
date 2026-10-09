# Observation / Interpretation / Learning Architecture

## Non-negotiable rule

The original observation is immutable. AI interpretation and learning annotations are separate records.

```text
IMMUTABLE OBSERVATION
        |
        | observation_id
        v
AI INTERPRETATION
        |
        +-- human_feedback
        +-- speaker_adaptation
        +-- pattern_learning
        +-- strategy_learning
        +-- ai_self_evaluation
```

### Observation
Contains only evidence derived from the recording and model execution: audio quality,
acoustic measurements, phoneme observations, temporal measurements, and raw model output.

### Interpretation
Contains candidate words, likely interpretation, confidence, uncertainty, context,
and rationale. It can be revised or superseded without changing the observation.

### Learning annotations
The five learning keys reference the observation by `observation_id`. They are not
permitted to overwrite observation fields.

This separation is required before moving Render analytics to the Parent PC.

## Recording and session traceability

Before audio is sent for analysis, the Android app creates a `sessionId` for the
current app session and a fresh `recordingId` for each recording. The analysis
server preserves both IDs and creates a separate `observationId`.

This gives the audit chain:

`sessionId -> recordingId -> observationId -> interpretations -> human feedback -> learning`

The IDs are identifiers only; they do not permit AI learning layers to rewrite
the immutable observation.

## Deep learning architecture — Phase 1 implemented

This build adds the first persistent learning foundation without allowing silent
self-training.

- Android creates and reuses an anonymous `speakerId`.
- Every recording is linked by `sessionId`, `recordingId`, and `observationId`.
- Immutable observations are stored append-only with a SHA-256 integrity hash.
- AI interpretations are stored separately from observations.
- Caregiver confirmation is linked back to the observation.
- Only an explicitly approved confirmation becomes a learning example.
- Approved examples update per-speaker word, pattern, and heard-to-meaning history.
- Future candidate ranking can receive a conservative boost from repeated,
  human-approved speaker-specific mappings.
- Confirmed outcomes feed basic self-evaluation statistics.
- No model weights are retrained automatically in this phase.

The learning chain is:

`audio -> immutable observation -> interpretation -> human confirmation -> approved example -> speaker profile -> future ranking`

This preserves the v6 rule that AI learning may add evidence and interpretation
but may not rewrite the original observation.
