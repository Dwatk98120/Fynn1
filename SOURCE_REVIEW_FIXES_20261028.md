# 0.4.19 source review fixes, 2026-10-28

Reanalysis previously accepted conflicting declared sources in same-ID copies,
and a top-level checksum skipped nested recording/speaker/source verification.
The checksum verifies bytes, not identity or provenance. Modern receipts now
require a known declared source and reject conflicting present nested source,
recording ID or speaker ID. All same-ID declared sources must agree before a
new analysis export is written. Source-absent legacy aliases still require a
separate verified receipt and retain unknown provenance. No metadata migration,
original WAV replacement, duplicate deletion or learning approval is introduced.

The synthetic check used by the source and frozen-build verifier now exercises
four conflicting modern receipts. Its output must explicitly confirm
`receiptConflictsRejected`; an older frozen executable cannot satisfy this
updated gate. Reanalysis integrity reports now label the build 0.4.19 instead
of 0.4.17. Historical reports are left unchanged.

Validation: 487 passed, 4 skipped; Android source guard and synthetic legacy-alias
build helper passed. See TEST_RESULTS_0.4.19.md for commands and limitations.
The original 0.4.19 source suite also passed in the supplied build environment
(466 passed, 4 skipped); earlier missing-dependency failures came from using
the base Python installation. No dependencies or environments were modified.

The received full source manifest already disagreed with `.gitignore`. Its exact
bytes are retained in SOURCE_MANIFEST_SHA256_0.4.19_BASELINE.json. The current
SOURCE_MANIFEST_SHA256.json is refreshed for the managed source/document files,
including the amended files, baseline manifest and this note. It excludes Git
metadata, caches, generated outputs and itself; no recording inventory is exposed.
SOURCE_RELEASE_0.4.19_VERIFICATION.json is unchanged historical proof for the
original 36 program files and original frozen build. It must not be used to
claim these amended program files match that executable.

The user authorized initializing this snapshot as a local repository on
`hearlium-parent-pc-integration`; the branch was confirmed before source edits.
No Main branch, commit, remote, push, installation or device data was changed.
New frozen build and installed-device acceptance remain pending. Existing adult
samples are not pediatric clinical validation.

Follow-up: PocketSphinx 5.0.4 is now installed inside the ignored local `.venv`.
The full suite passes with **488 passed, 3 skipped**, and `pip check` passes.
Native bundled-engine/dictionary initialization is verified; the remaining
skips require original private adult audio/metadata. Actual recording alignment
and frozen-build packaging remain separate checks. This venv reads the other
dependencies from the supplied 0.4.12 build environment through a local `.pth`
file; no original environment, recordings or metadata were modified.
