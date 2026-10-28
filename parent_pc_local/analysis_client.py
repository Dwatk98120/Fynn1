"""Reliable Windows local API job client with polling and recoverable failure.

Upload once; do not POST audio again just because a model is loading slowly.
The WAV is always retained on disk by direct_recording before submission.
"""
from __future__ import annotations

import time
from pathlib import Path
import requests
try:
    from api_diagnostics import write_event
except ModuleNotFoundError:  # importlib tests load this file without its folder on sys.path
    from parent_pc_local.api_diagnostics import write_event


class AnalysisStillRunning(RuntimeError):
    pass


def analyze_saved_wav(api_base, wav_path, params, progress=None,
                      max_wait_seconds=20 * 60, poll_seconds=1.5, session=None):
    req = session or requests
    api_base = api_base.rstrip("/")
    wav_path = Path(wav_path)
    if not wav_path.is_file():
        raise FileNotFoundError(f"Saved recording not found: {wav_path}")
    if progress:
        progress("Submitting saved recording to local server")
    try:
        with wav_path.open("rb") as file:
            # Explicit endpoint prevents lost/misinterpreted reanalysis flags.
            is_reanalysis = str(params.get("reanalysis", "false")).lower() == "true"
            endpoint = "/v1/reanalysis-jobs" if is_reanalysis else "/v1/analysis-jobs"
            response = req.post(f"{api_base}{endpoint}",
                                files={"audio": (wav_path.name, file, "audio/wav")},
                                data=params, timeout=(10, 30))
    except (requests.ConnectionError, requests.Timeout) as exc:
        write_event("analysis_submission_connection_failed", errorType=type(exc).__name__)
        raise
    if response.status_code >= 500:
        write_event("analysis_submission_server_error", httpStatus=response.status_code)
    if response.status_code == 404:
        raise RuntimeError("The Parent PC server is an older version. Restart the Phase 2 hotfix server.")
    response.raise_for_status()
    submitted = response.json()
    job_id = submitted.get("jobId")
    if not job_id:
        raise RuntimeError("Server did not return an analysis job ID")

    started = time.monotonic()
    last_stage = ""
    last_update = 0.0
    connection_errors = 0
    while True:
        if time.monotonic() - started > max_wait_seconds:
            raise AnalysisStillRunning(
                "Analysis has taken unusually long. Your WAV is saved. "
                f"Job ID: {job_id}. Check parent_pc_server.log; do not delete the recording."
            )
        try:
            response = req.get(f"{api_base}/v1/analysis-jobs/{job_id}", timeout=(5, 15))
            if response.status_code == 404:
                raise RuntimeError("Server was restarted and the pending job was lost. "
                                   "The WAV is safe; restart analysis from Recording History.")
            if response.status_code >= 500:
                write_event("analysis_poll_server_error", httpStatus=response.status_code)
            response.raise_for_status()
            state = response.json()
            if connection_errors:
                write_event("analysis_poll_connection_recovered", failedProbes=connection_errors)
            connection_errors = 0
        except (requests.ConnectionError, requests.Timeout) as exc:
            connection_errors += 1
            if connection_errors == 1 or connection_errors == 4:
                write_event("analysis_poll_connection_failed", errorType=type(exc).__name__,
                            attempts=connection_errors)
            if progress:
                progress("Reconnecting to local server; recording remains saved")
            if connection_errors >= 4:
                raise RuntimeError("Local server stopped responding while processing. "
                                   f"WAV is safe. Job ID: {job_id}") from exc
            time.sleep(poll_seconds)
            continue

        status = state.get("status")
        stage = state.get("stage") or status or "Working"
        # Continue updating the UI during a long cold load, not only when the
        # stage changes. A fixed 'Analyzing...' label was the original symptom.
        now = time.monotonic()
        if progress and (stage != last_stage or now - last_update >= 5):
            progress(f"Analysis: {stage} ({int(state.get('elapsedSeconds', 0))}s)")
            last_stage, last_update = stage, now
        if status == "completed":
            result = state.get("result")
            if not isinstance(result, dict):
                raise RuntimeError("Analysis job completed without a valid result")
            if str(params.get("reanalysis", "false")).lower() == "true":
                storage = result.get("recordingStorage") or {}
                if not (storage.get("reused") is True
                        and storage.get("reanalysis") is True
                        and storage.get("source") == params.get("recording_source", "parent_pc")):
                    write_event("reanalysis_storage_ack_missing", jobId=job_id)
                    raise RuntimeError(
                        "Reanalysis storage protection was not acknowledged by the local server. "
                        "Stop reanalysis and verify the installed server version and recording folder. "
                        "Do not delete any WAV files.")
            return result
        if status == "failed":
            raise RuntimeError(f"Analysis failed: {state.get('error') or 'unknown error'}. "
                               "See parent_pc_server.log; WAV was retained.")
        if status not in ("queued", "running"):
            raise RuntimeError(f"Unexpected analysis job status: {status!r}")
        time.sleep(poll_seconds)
