# Hearlium Branch 2 — Phase 3 Analysis & Feedback Consistency Hotfix

**Date:** 2026-10-23  
**Baseline:** `Hearlium_Branch2_Phase3_Student_Recording_Search_Android_Phoneme_Wording_20261023.zip`  
**Scope:** Parent PC analysis and caregiver feedback synchronization, Android recording review compatibility  
**Main branch:** not changed. **Phase 2 baseline:** not changed.

## Corrections

1. **Accepted feedback for an obsolete observation cannot approve the new one.** The app records the submitted observation ID, checks it under the per-recording metadata lock when the response arrives, and rejects updates if the observation changed. An accepted response to the prior observation is saved in an observation-specific audit file at `%LOCALAPPDATA%\Hearlium\ParentPC\feedback_observation_audit`, and the caregiver is warned to review the latest analysis anew. This does not undo the API's already-accepted entry for the older observation.
2. **Android results can be loaded without reanalysis.** `Load into Review` now checks the separate verified export in `analysis_results/<recording-stem>_analysis.json` if the inline metadata has no `analysisResult`. The loader verifies observation ID, optional recording ID, and source WAV path before showing suggestions; mismatches are rejected. Recording History can also search Android's original unverified word suggestions.
3. **Stale analyses cannot write results.** Each manual analysis increments an analysis-generation token and clears the old on-screen result before starting. The active request is checked inside a synchronization lock *before* any result or metadata is committed. Out-of-order responses are dropped without replacing the latest metadata or export. Approved caregiver decisions associated with an older observation are retained under `previousAnalysisReviews` and are not carried forward as approvals of the new observation.
4. **Analysis exports are versioned and written atomically.** Metadata points to an immutable versioned export; the conventional `_analysis.json` file is maintained as a compatibility mirror for existing analytics. A failed metadata commit removes the unpublished version without disturbing the previously committed export.
5. **While reanalysis is running, word review, unsure/reject controls and network feedback are blocked** until results are available. The original WAV is never overwritten by these changes.

## What remains unchanged

- The latest student search, name-filtering UI, and safer ID handling remain included.
- The Android phoneme wording improvement and Android source are unchanged.
- Phase 3 API diagnostic logs, previous recording-overwrite protections, and versioned caregiver word-review manifests remain included.
- No automatic model training is introduced; only explicit caregiver confirmation may contribute to future verified learning.
- The underlying intermittent API dropout is **not** claimed fixed by this hotfix.

## Automated validation in this build environment

- `PYTHONPATH=parent_pc_local:server python -m pytest -q server/tests`: **110 passed, 8 subtests passed**.
- `PYTHONPATH=parent_pc_local:server python -m unittest discover -s server/tests -p 'test_*.py' -q`: **90 passed**.
- Live Tkinter GUI smoke test with a virtual display: **passed** for Android export review, searchable original suggestions, and immediately invalidated older analyses.
- Python compile check and ZIP archive integrity checks: **passed**.

**Windows installer compilation and Android APK compilation were not run here.** The included `BUILD_HEARLIUM_INSTALLER.bat` performs the Windows build and its own test gate. The Android source is unchanged from the preceding package, so no APK change is required for this Parent PC-specific repair.

## Windows build instructions

1. Keep the previous stable ZIPs as backups. Extract this ZIP to a new short path, such as `C:\Hearlium3` (do not merge source directories).
2. Run `BUILD_HEARLIUM_INSTALLER.bat` from the extracted folder using your established GitHub/Windows workflow.
3. After a successful compile, install `installer\output\HearliumSetup.exe`.
4. Keep Main frozen. Apply source changes only to Branch 2 if committing to GitHub.

## Live safety verification checklist (use disposable test recordings)

1. **Android import:** Select an Android recording that has a saved analysis export. `Load into Review` should display the original suggested words immediately; its observation ID must match the recording, and the WAV must be unchanged. Search its suggested words in Recording History.
2. **Reanalysis:** Load a recorded sample, select Analyze Recording twice at different times or reanalyze it from history. The previous results must disappear as soon as the newer request begins; no old response should overwrite the latest saved analysis.
3. **Feedback boundary:** Submit feedback only while the analysis is idle. If an observation changes before the API returns, the app must report that the feedback belongs to an older observation and not mark the current one approved. The audit record should be under `feedback_observation_audit`.
4. **Review history:** Check that earlier review history remains accessible and a changed observation requires new caregiver approval. Do not automatically carry over confirmations.
5. **Connection reliability:** Continue capturing API diagnostics if intermittent connection refusal recurs. This fix does not address root-cause server termination.

Do not approve new personalized-learning examples until the real-PC safety checks and connection stability are satisfactory. Existing student audio and saved evidence should be backed up before installer replacement.
