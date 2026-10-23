HEARLIUM — PHASE 3 WINDOWS STARTUP-PROGRESS + PHASE 2 RELIABILITY HOTFIX
Build 2 / Branch 2 only | 2026-10-22 | source ZIP, not a built installer

WHY
Previous Phases 1, 2 and 3 could spend about four minutes before the Parent PC
reported "Server running". The frozen local server imported large speech libraries
before exposing its health endpoint. The elapsed time can also include Windows
security checks, imports, and offline model initialization; the actual cause on
this PC has NOT been proven.

CHANGES
1. Lightweight local API bootstrap. Uvicorn can expose GET /health before
   importing large Torch/Transformers/phoneme modules in a background thread.
   While importing, the JSON says ok:false/serverPhase:initializing and any
   analysis attempt receives HTTP 503 + Retry-After. It never claims to be ready.
2. Parent PC startup status updates with elapsed seconds, including API import,
   offline phoneme model load, word model load, ready/partial/error.
   Startup stage timings and exceptions are in parent_pc_server.log.
3. Restores Phase 2 cold-start repair within Phase 3:
   - bundled offline phoneme and Faster-Whisper models
   - model preloading off the server event loop
   - queued analysis jobs, duplicate-job protection, progress polling
   - Windows saved WAV preserved, Android endpoints unchanged
4. Preserves Phase 3 caregiver-approved personalized learning, learning ledger,
   history, rollback, and 13-layer health dashboard.
5. Regression gate runs full pytest suite in the clean installer venv, not only
   unittest discovery, so end users do not need to install pytest or NumPy globally.
6. Legacy candidate segments with NO segment indices are read by position only
   when the whole candidate array is unindexed. Explicitly indexed candidates
   are never guessed/realigned for training.
7. Inno Setup version increases to 0.4.1; AppId unchanged so upgrades target
   the same application. No migrations or automatic learning.

IMPORTANT LIMITATIONS
- This addresses apparent startup dead time and adds truthful readiness status.
  It CANNOT guarantee that loading models is faster on a given Windows PC.
  The first-run loading may still take minutes; it will no longer look like an
  unresponsive server during heavy module import.
- It has NOT been compiled or installed on Windows in this environment.
- This is NOT a new Android APK; the original app directory is unchanged.
- Existing LOCALAPPDATA/Hearlium/ParentPC recordings, observations and ledgers
  are outside the installer source folder and must be preserved.
- The Android LAN service still needs the Parent PC to be reachable on the LAN;
  Windows-made recordings remain offline capable.
- The prior recognition-ranking issue ("want" mistakenly ranked "one") remains
  a separate backlog item. No claim of validated speech accuracy.

BUILD ON WINDOWS
1. Keep your previous Phase 2 and Phase 3 source ZIPs and installers backed up.
2. Extract this ZIP into its OWN NEW folder (do not overwrite the old source).
3. Run BUILD_HEARLIUM_INSTALLER.bat on Windows with network access at build time
   (offline models and official VC++ redist are staged at build time).
4. Confirm "Regression suite passed", Inno "Successful compile", BUILD COMPLETE.
5. Install installer\output\HearliumSetup.exe. Save any important existing data
   beforehand; installing in the same path replaces existing application binaries.
6. Wi-Fi off (only for Parent PC), restart the app, press Start Parent PC.
   Expect "Local API listening / importing" then "Server running / Loading AI"
   then "Server running / AI models ready". Record elapsed seconds at each stage.
7. Make the FIRST short recording, verify analysis and original WAV persistence.
8. Verify Phase 3 Learning History and 13-Layer Health still work, and verify
   Android connection separately on local Wi-Fi when it is re-enabled.

LOG FOR PROBLEMS
%LOCALAPPDATA%\Hearlium\ParentPC\parent_pc_server.log
Do not delete recordings, caregiver approvals, or learning data to troubleshoot.

TESTS RUN ON LINUX SOURCE
58 pytest tests passed; 38 unittest tests passed. Gateway behavior is tested
with fake server apps and without audio models. No Windows startup duration
or model-loading performance was measured here.

SOURCE PROTECTION
Working Phase 2 and Phase 3 remain as separate protected backups; changes are
intended for Branch 2 only. Main remains untouched.
