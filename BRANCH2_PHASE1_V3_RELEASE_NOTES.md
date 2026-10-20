# Branch 2 — Phase 1 + word-level review v3

- Adds review-only `proposedWordAlignment`, derived from Faster-Whisper's English hypothesis and existing CTC segment time span.
- Word intervals are **pronunciation-weighted estimates**, NOT verified forced alignment; every boundary is uncertain and cannot be approved for pronunciation learning.
- Parent PC defaults to a proposed complete-word review when available; an Advanced button retains the original CTC-fragment review.
- Expanded everyday candidate vocabulary. Existing candidate engine weak-match rejection and IPA classification are retained.
- No model retraining, no rewriting immutable observations, no edits to Main.

## Known limitations

This is an intermediate safety-first alignment UI, not acoustic forced alignment. Estimated clips may contain neighboring words. Future phase: validated forced alignment with uncertainty scoring and protected benchmarks. Confirming the whole sentence remains separate from approval of individual pronunciation examples.

Build the APK and Parent PC installer using existing repository workflows. Test on real audio before distribution.
