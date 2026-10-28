"""Minimal, privacy-conscious diagnostics for Hearlium's local API.

Emits transition-oriented JSON lines, not WAV data, transcripts, student IDs or
caregiver decisions. A separate entry is created by each cooperating process.
No network or extra package is required. These logs stay on the Windows PC.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import subprocess
from pathlib import Path
import time

DATA_DIR = Path(os.getenv("LOCALAPPDATA") or str(Path.home())) / "Hearlium" / "ParentPC"
EVENTS_FILE = DATA_DIR / "api_connection_events.jsonl"


def write_event(event: str, **details):
    """Append one small, non-sensitive event; never interrupt operation for logging."""
    allowed = (str, int, float, bool, type(None))
    entry = {
        "timestampUtc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "pid": os.getpid(), "event": str(event)[:72],
    }
    for key, value in details.items():
        if isinstance(value, allowed) and len(key) <= 48:
            # Do not record audio paths, utterances or patient-identifying payloads.
            entry[key] = value[:180] if isinstance(value, str) else value
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        line = (json.dumps(entry, ensure_ascii=True, separators=(",", ":")) + "\n").encode("utf-8")
        handle = os.open(str(EVENTS_FILE), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        try:
            os.write(handle, line)
        finally:
            os.close(handle)
    except OSError:
        # Never break the recording application because Windows denies log writes.
        pass


def classify_health(document):
    """Return (state, display stage), without trusting HTTP 200 as readiness."""
    if not isinstance(document, dict):
        return "invalid_response", "Invalid health response"
    phase = document.get("serverPhase")
    if phase == "failed":
        return "startup_failed", "API startup failed"
    if phase == "initializing":
        return "initializing", "Loading API modules"
    if phase != "serving" or document.get("ok") is not True:
        return "invalid_response", "Unexpected API response"
    models = document.get("modelLoading")
    if not isinstance(models, dict):
        return "api_ready", "API responding"
    status = models.get("status")
    if status == "ready":
        return "ready", "AI models ready"
    if status == "error":
        return "model_error", "AI model error"
    if status == "partial":
        return "partial", "Word model unavailable"
    return "model_loading", "Loading AI models"


class ConnectionTimeline:
    """Writes state transitions and sparse continued-failure reminders."""
    def __init__(self, emit=write_event, reminder_seconds=300, clock=time.monotonic):
        self.emit = emit
        self.clock = clock
        self.reminder_seconds = reminder_seconds
        self.state = None
        self.last_event = None
        self.first_failure = None
        self.failures = 0

    def observe(self, state, **details):
        now = self.clock()
        is_bad = state in ("offline", "invalid_response", "startup_failed", "model_error", "partial")
        if is_bad:
            if self.first_failure is None:
                self.first_failure = now
            self.failures += 1
        else:
            if self.first_failure is not None and self.state is not None:
                self.emit("api_recovered", previous=self.state,
                          outageSeconds=round(now - self.first_failure, 1), failures=self.failures)
            self.first_failure = None
            self.failures = 0
        changed = state != self.state
        if changed or (is_bad and self.last_event is not None and now - self.last_event >= self.reminder_seconds):
            self.emit("api_state_changed" if changed else "api_still_unhealthy",
                      previous=self.state or "none", state=state,
                      consecutiveFailures=self.failures, **details)
            self.last_event = now
        self.state = state


def parse_windows_netstat(output, port=8000):
    """Parse Windows netstat -ano and return listener PID (or None)."""
    for line in output.splitlines():
        fields = line.split()
        if len(fields) < 5 or fields[0].upper() != "TCP":
            continue
        if fields[3].upper() != "LISTENING":
            continue
        if fields[1].rsplit(":", 1)[-1] != str(port):
            continue
        try:
            return int(fields[4])
        except ValueError:
            continue
    return None


def windows_listener_pid(port=8000):
    """One bounded local snapshot; called only when the health state drops."""
    if os.name != "nt":
        return None
    try:
        result = subprocess.run(["netstat", "-ano", "-p", "TCP"],
                                capture_output=True, text=True, timeout=4,
                                creationflags=subprocess.CREATE_NO_WINDOW,
                                check=False)
        return parse_windows_netstat(result.stdout, port)
    except (OSError, subprocess.TimeoutExpired):
        return None
