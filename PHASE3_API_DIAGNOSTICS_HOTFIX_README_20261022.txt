HEARLIUM — BRANCH 2 / PHASE 3 API DROPOUT DIAGNOSTICS HOTFIX
Build 0.4.2 | October 22, 2026 | FULL SOURCE ZIP (not compiled Windows EXE)

PURPOSE
The October 22 Phase 3 caregiver feedback submission failed with Windows
WinError 10061 (localhost:8000 refused the connection), yet the main Parent PC
window was open. No matching Windows Application Error was found for that time.
The exact cause is unproven. This hotfix CAPTURES the next failure; it does not
claim to fix the underlying reason for process termination or server hangs.

THE VERIFIED CODE GAP
The previous Parent PC launcher stopped probing GET /health as soon as the
server reported its AI models were ready. A later crash or port dropout could
therefore go undetected in the launcher and the display could remain stale.
This hotfix monitors every 3 seconds for the entire server session.

WHAT IS CHANGED
  * Phase 3 launcher continues /health monitoring after AI readiness.
  * State transitions recorded with local timestamps (UTC), process PID, health
    response time, error class, WinError/errno when present, and elapsed time.
  * Process exits captured with exit code; intentional Stop is distinguished
    from unexpected termination as far as the launcher remains alive.
  * On a new connection outage, Windows netstat port 8000 listener PID is
    captured to distinguish unbound port from unresponsive owned process.
  * An independent server heartbeat is logged every 60 seconds, with uptime.
  * API startup/import errors, Python exceptions and fatal tracebacks go to
    persistent logs, including early stdout/stderr from the server process.
  * Recording-window feedback save errors, health-connection test failures,
    queued analysis submission failures, and analysis polling 5xx/dropouts get
    metadata-only diagnostic entries (no audio, transcripts, student identity
    or caregiver decision text).
  * Parent PC main window has "Open API Diagnostic Logs" to open the folder.
  * HTTP access logging is disabled; diagnostics do not POST data off the PC.
  * Source-mode API starter now uses the same lightweight gateway/logger as the
    packaged EXE. All existing Phase 3 learning ledger/rollback, Phase 2 queue,
    and Android source are unchanged.

NOT CHANGED
  * No automatic restart of a crashed server (diagnostics first).
  * No automatic retry of caregiver feedback, audio uploads, or learning;
    unknown save outcomes must be checked before resubmission.
  * No change to model accuracy, recognition, phoneme decisions, local data,
    recordings, confirmed clips, approved learning or rollback behavior.
  * No changes to Main or the earlier Phase 2 source baseline.

BUILD ON WINDOWS (the builder needs network to download build dependencies)
1. Keep your working Phase 2 and Phase 3 source ZIPs and any important recordings
   backed up. Do not delete %LOCALAPPDATA%\Hearlium\ParentPC.
2. Extract THIS full-source ZIP into a separate NEW directory.
3. Import/upload that source into the existing Branch 2 GitHub branch only;
   never merge it into frozen Main. The installer is also buildable locally.
4. Run BUILD_HEARLIUM_INSTALLER.bat in the extracted root directory.
5. Confirm regression tests passed and Inno Setup reported Successful compile.
6. Install installer\output\HearliumSetup.exe. Existing AppId is retained.
7. Open Hearlium Parent PC, press Start Parent PC, check status transitions.
8. Leave the main window open when running reviews so it can monitor the child
   server. Run your normal test recordings. Do not force an outage during a
   caregiver save.

HOW TO CHECK A DROPOUT
1. DO NOT uninstall, clear data, or repeatedly click Submit feedback.
2. In the main Parent PC window click "Open API Diagnostic Logs".
3. Read these files under %LOCALAPPDATA%\Hearlium\ParentPC:
   api_connection_events.jsonl     Timed status changes and process exits
   parent_pc_server.log          Python startup, model and server errors
   parent_pc_server_console.log  Server stdout/stderr before Python logging
   parent_pc_server_fatal.log    Python's fatal-signal tracebacks if available
4. Preserve all four files (and their last-modified times); copy them before
   replacing the installer so their timeline is retained.
5. Share the relevant log files for inspection after reviewing them for any
   potentially sensitive paths or traceback data. Logs remain local until
   deliberately shared. None of the logs are evidence of a successful save.
6. Note the exact Windows clock time and which action was being taken.

EXAMPLE EVENT SEQUENCE
  server_process_started ... serverPid=1234
  api_state_changed ... state=initializing
  api_state_changed ... state=ready
  api_state_changed ... state=offline, reasonType=ConnectionRefusedError
  api_port_snapshot ... listeningPid=null, expectedPid=1234
  server_process_exited ... exitCode=... expected=false
If the process remains alive but the API is offline, the status says "API
connection lost" and monitoring continues; a later recovery is logged.

VALIDATION
63 Python source regression tests passed (pytest); 43 unittest tests passed.
Tests cover ready -> offline -> recovered, invalid readiness, sparse reminders,
netstat listener PID parsing and source guardrails. Windows .exe/Inno Setup
compilation and actual Windows outage behavior CANNOT be verified in this
container and still require validation on the user's Parent PC.

SAFETY
Logs may include stack traces/Windows paths. Review before uploading.
Original recordings, evidence, caregiver-confirmed learning and audit ledgers
under LOCALAPPDATA must be protected. No personal data is automatically sent.
This is a DIAGNOSTICS hotfix; resolving root cause will follow collected logs.
