NOTE: This describes the older Phase 3 Build 1 baseline.
For the latest startup and Phase 2 reliability changes, read
PHASE3_STARTUP_PROGRESS_HOTFIX_README_20261022.txt first.

HEARLIUM PHASE 3 - WINDOWS PARENT PC BUILD 1 (SOURCE)
========================================================
Based on protected Phase 2 Build 1 source. Main branch must remain frozen.
Do not rebuild Android yet; Phase 3 Build 1 changes are Windows/Parent PC only.

WHAT IS ADDED
- Only explicitly caregiver-approved SINGLE-WORD examples from valid observations
  update a speaker's pronunciation dictionary and candidate-ranking history.
- Multiword recordings require an explicit segment index for learning.
- Repeat approval (such as tapping twice) is idempotent and does NOT train twice.
- Conflicting approval for the same segment requires explicit rollback first.
- Revocation is append-only, preserves original observation/audio/approval history,
  recomputes active speaker ranking preferences, and supports reapproval.
- New Parent PC GUI buttons: Phase 3 Learning History, 13-Layer Health.
- Localhost-only detailed approval history and rollback API endpoints.
- 13-layer operational presence dashboard; NO unmeasured accuracy claims.
- Existing homophone ranking retained, always review-only.
- 34 Python regression tests passed in development environment.

HOW TO BUILD - WINDOWS
1. Keep the working Phase 1 Windows app and installer backed up.
2. Extract this ZIP to a NEW folder. Do not extract on top of old Phase 1.
3. Use Branch 2; never overwrite Main with this source.
4. Double-click BUILD_HEARLIUM_INSTALLER.bat.
5. The builder runs source regression tests BEFORE downloading dependencies.
6. It then runs Python/PyInstaller, checks the frozen executable, and
   compiles Inno Setup if Python 3.12, .NET 8 SDK, Inno Setup 6, and all
   model/native dependencies are present.
7. SUCCESS requires a completed Inno Setup build and a file at:
   installer\output\HearliumSetup.exe
8. Report the Windows build result before installing/updating Android APK.

IN THE WINDOWS APP
- Start Parent PC, then choose Phase 3 Learning History.
- Select a speaker ID (populates from locally saved observations), Refresh.
- Only approved single-word examples appear; Confirm & Save of a whole
  sentence is NOT a pronunciation-training approval.
- Select an ACTIVE example and choose Revoke to roll back that example.
- The 13-Layer Health view shows which component data appeared in the most
  recent completed analysis; accuracy remains unmeasured without benchmarks.

LOCAL API (PARENT PC ONLY FOR PRIVATE HISTORY/ROLLBACK)
GET  http://127.0.0.1:8000/v1/learning/speakers
GET  http://127.0.0.1:8000/v1/learning/examples/<speaker_id>
POST http://127.0.0.1:8000/v1/learning/revoke
GET  http://127.0.0.1:8000/v1/layers/health
Existing Android POST /v1/learning/feedback remains compatible.

IMPORTANT LIMITATIONS
- This ZIP is SOURCE, not a finished or Windows-tested installer.
- Python tests verify logic; native Windows, .NET, Inno Setup, microphone,
  model initialization and real-device communication require local testing.
- The health dashboard reports activity, not calibrated precision/accuracy.
- Full new Silero VAD and a *second* independent Wav2Vec2 recognizer are
  NOT bundled. The existing independent phoneme recognizer remains intact.
- Further Phase 2 word-ranking issues (I/want, candidate duplicates) remain
  on the repair list; this Phase 3 build does not claim to fix them.
- Current bundled VC++ runtime and AAC installer behavior are unchanged.
- Review commercial redistribution rights for models/dependencies before release.
- Audio and all processing stay on the Windows PC; do not expose port 8000
  to the public internet. Limit access to trusted local-network clients.

ROLLBACK
- Preserve the original working installer and data folder.
- Approval rollback records are appended; they never delete evidence.
- Windows build/test does not automatically touch the installed app.
