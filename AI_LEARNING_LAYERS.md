# AI Learning Layers 9–13

## Core rule: observations are immutable

First Sound Helper separates **observation** from **interpretation** and **learning**.

The original observation is captured with an ID and timestamp and includes the original transcript, observed phonemes, raw evidence, and audio-derived features. Later learning cannot replace those values.

A human correction is stored separately. For example:

- Observation: model heard an uncertain final consonant.
- AI interpretation: candidate = `cat`.
- Human feedback: `confirmedWord = cat`.

The human feedback does **not** rewrite the observation.

## Layer 9 — Human Feedback
Creates labeled examples from parent/teacher confirmation or correction.

## Layer 10 — Speaker Adaptation
Learns speaker-specific word and pattern history. Adaptation can influence future confidence, but never changes historical observations.

## Layer 11 — Pattern Learning
Aggregates repeated words and pronunciation patterns and only marks learning readiness after enough examples.

## Layer 12 — Strategy Learning
Tracks which support strategies appear successful and can recommend a next strategy when enough evidence exists.

## Layer 13 — Self-Evaluation
Measures confirmed accuracy and indicates when there are enough evaluated examples to consider calibration.

These layers are learning aids and engineering signals, not clinical determinations.
