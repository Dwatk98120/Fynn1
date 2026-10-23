# Hearlium Branch 2 — Phase 3 Recording & Review Audit Safety Follow-up (2026-10-22)

**Base:** Complete Phase 3 Evidence Integrity Hotfix v0.4.3, including Phase 3 caregiver-review usability and API diagnostics. **Main frozen; Phase 2 baseline unchanged.** No Android changes.

## What this source hotfix repairs

1. **Recording destination protection:** A recording gets its own immutable target path on start, with a microsecond timestamp and a random suffix. Stop writes exclusively to that path (`xb`) and cannot truncate an existing WAV. Recording History buttons are disabled during recording, and history-changing operations also enforce the lock in their handlers. If recording details fail to save, the original WAV is retained and an explanatory error is displayed.
2. **Review/audio alignment:** Previously saved word decisions are reloaded only when their observation ID, segment index, start/end time, suggested word and observed phonemes match the current analysis. Legacy reviews without an observation ID cannot silently reapprove a newly analyzed clip. A review window opened before a recording/analysis switch refuses to save; reopen it to review current clips. Prior decisions remain on disk.
3. **Synchronized metadata updates:** Metadata updates from analysis, API feedback and local review actions now use a per-recording reentrant lock with an atomic read-modify-write operation. Each atomic file save gets a unique `.tmp` filename, preventing staging collisions between threads of the Parent PC recording app. This is **in-process synchronization**, not a claim of cross-process distributed locking.
4. **Review history preserved:** Before the current review manifest is replaced, its exact bytes are archived in `segment_reviews/history/<recording>_segments/`. Archived JSON contains earlier decisions, observation ID, timings, word labels and approved clip paths. Prior clips remain immutable. Archives are staged privately before publishing. Existing review files overwritten in previous versions cannot be reconstructed retroactively.

## Safety and scope

- A caregiver confirmation is **not** automatic AI model training. Ambiguous or changed observations require renewed review.
- No original WAVs are altered by review/approval; previous approved clips remain available.
- API monitoring and diagnostic logging remain present. These changes do not establish the root cause of the random API disconnects.
- Review snapshots are available for audit and future manual recovery; **there is not yet a one-click rollback UI**.
- Backup the existing installation's data before switching releases, and test with nonessential example recordings first.

## Validation

- `PYTHONPATH=parent_pc_local:server python -m pytest -q server/tests` — 87 passed in this environment.
- Tkinter window smoke test under Xvfb — passed. History controls disable/re-enable correctly.
- Windows PyInstaller / Inno Setup build **not performed** here; Windows installer must still be built and tested on the PC.
- New tests cover recording target isolation, metadata concurrency, changed word timings/observation IDs, immutable review-history snapshots, and failed review-manifest publication.

## Building on Windows

1. Extract into a clean, **short** path, e.g. `C:\Hearlium3`.
2. Run `BUILD_HEARLIUM_INSTALLER.bat`. It obtains the official VC++ runtime prerequisite for distribution (it does not install the redistributable on the build PC).
3. After a successful build, run `installer\output\HearliumSetup.exe` to install the new version.
4. Verify the updated recording/history and review workflows with disposable test audio before resuming personalized-learning approvals.
