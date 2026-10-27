# Hearlium — GitHub-ready 0.4.19 source snapshot

This folder was assembled from `SAVED_LIVE_SESSION_SUMMARIES.zip` (0.4.19 snapshot) and includes the archive-comparison report under `docs/archive-comparison/`.

**Important:** This is a candidate source snapshot, **not** a tested Git checkout, and has **not** been committed or pushed. Main must remain frozen. The intended development branch is `hearlium-parent-pc-integration` (Branch 2).

## Before uploading
1. Open the existing repository and verify the correct branch and commit; create a backup branch/tag before any merge.
2. Compare this snapshot against current Branch 2 source. **Do not blindly overwrite the existing repository.**
3. Review all tracked files for secrets, personal information, and licensing. This packaging step excluded common credential filenames but did not constitute a complete security audit.
4. Review `BUILD_0.4.19_README.txt`, `SOURCE_MANIFEST_SHA256.json`, `SOURCE_RELEASE_0.4.19_VERIFICATION.json`, and `TEST_RESULTS_0.4.19.md` where present.
5. Run the source tests and build checks on the actual branch; verify installer and Android separately.
6. Preserve all original WAV evidence, recording identities, caregiver approvals, and historical results.

## Packaging exclusions
`.installer_venv/` (5,198 entries), caches, compiled binaries, local logs, WAV files, and common credential files were excluded. Recreate dependencies in the build environment instead of committing them. See `.gitignore`.

## Safety and status
0.4.19 reports 463 passing tests and 3 skipped, but this package has **not** independently rerun them. Installed-device acceptance remains pending. The previous comparison found matching 0.4.19 source across the two archives, with older top-level recovery files that should not replace this snapshot.
