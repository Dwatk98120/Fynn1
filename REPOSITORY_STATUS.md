# Current source handoff - 0.4.21 - 2026-10-28

Current release: Parent PC **0.4.21**, Android **3.3.4/code10**.
Read [BUILD_0.4.21_README.txt](BUILD_0.4.21_README.txt),
[TEST_RESULTS_0.4.21.md](TEST_RESULTS_0.4.21.md) and
[GITHUB_0.4.21_UPLOAD.md](GITHUB_0.4.21_UPLOAD.md).
The complete offline NLTK resources are verified and pronunciation conversion
is exercised before readiness. Android removes local recording audio only after
fresh PC-copy verification and caregiver confirmation; metadata/audits stay.
Source suite: **517 passed, 3 skipped**; **12 real Kotlin policy/storage tests passed**.
Use only `hearlium-parent-pc-integration`; Main remains frozen. Remote APK build,
existing signing-key compatibility and installed-device acceptance remain pending.

## Historical handoff notes

# Current source handoff - 0.4.20 - 2026-10-28

Parent PC 0.4.20 source and build preparation supersedes the historical notes
below. See TEST_RESULTS_0.4.20.md and SOURCE_RELEASE_0.4.20_VERIFICATION.json
for current validation. Source suite: 493 passed, 3 optional private-audio skips.
APK workflows and wrapper agree on SHA-256-pinned Gradle 8.9. Android remains
3.3.3/code9; remote APK build and installed-device acceptance are pending.
Use GITHUB_0.4.20_UPLOAD.md to upload the source-only package to Branch 2.

## Historical 0.4.19 source review

Source amended 2026-10-28 on locally initialized `hearlium-parent-pc-integration`.
Current source suite: **488 passed, 3 skipped**, including native PocketSphinx
5.0.4 engine/dictionary initialization; Android and extended synthetic
receipt-conflict source checks pass. Reanalysis now rejects contradictory modern
receipt identities/provenance and conflicting same-ID declared sources; integrity
reports identify 0.4.19. See SOURCE_REVIEW_FIXES_20261028.md.
The release/frozen claims below are historical. Rebuild and installed-device
acceptance remain pending for this revised source.

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
