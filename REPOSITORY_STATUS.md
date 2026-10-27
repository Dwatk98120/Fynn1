# Current source handoff - 2026-10-27

Parent PC: **0.4.19**, cumulative through the Legacy Recording Alias Repair.
Android: **3.3.3/code9**, unchanged by this hotfix.
Source regression suite: **463 passed, 3 skipped**. Staged source and matching
frozen executable checks passed; see TEST_RESULTS_0.4.19.md and the exact source
hash proof in SOURCE_RELEASE_0.4.19_VERIFICATION.json. Installed-device acceptance
remains pending. No installation or remote Git state is claimed.

The reanalysis repair accepts only corroborated source-absent legacy aliases,
checks every same-ID copy, selects a fully verified canonical receipt and preserves
unknown legacy provenance. Conflicting identity/hash/source, truncated audio and
uncorroborated aliases remain failures. Original WAVs, metadata and history are
not migrated or rewritten.

PocketSphinx 5.0.4 provides optional timing against an explicitly confirmed
reference; it provides no independent word or pronunciation verification. Its
separate JSON does not change raw phonemes, ASR output, original audio or learning.

This is source only. Binaries, dependencies, model weights, recordings and private
validation reports are excluded. The Gradle wrapper scripts/properties are present,
the wrapper JAR is absent, and current workflows regenerate it. Android compilation,
remote workflow success and APK availability have not been verified by this handoff.
Use GITHUB_UPDATE_INSTRUCTIONS.md; preserve Main and unrelated local work.
