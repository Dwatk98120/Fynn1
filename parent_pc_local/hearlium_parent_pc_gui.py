from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
import json
import urllib.error
import urllib.request
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from api_diagnostics import write_event, ConnectionTimeline, classify_health, windows_listener_pid

FROZEN = bool(getattr(sys, "frozen", False))
ROOT = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parents[1]
USER_DATA = Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "Hearlium" / "ParentPC"
API_SCRIPT = ROOT / "parent_pc_local" / "start_parent_pc_server.py"
DIRECT_RECORDING = ROOT / "parent_pc_local" / "direct_recording.py"
PAIR_PHONE = ROOT / "parent_pc_local" / "pair_phone.py"
DATA_DIR = USER_DATA
BT_EXE = (
    ROOT / "HearliumBluetoothService.exe"
)

class HearliumParentPC(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hearlium Parent PC")
        self.geometry("660x690")
        self.minsize(660, 650)

        self.api_proc = None
        self.bt_proc = None
        self._monitor_generation = 0  # invalidates older monitor threads
        self._stop_requested = False

        tk.Label(self, text="Hearlium Parent PC", font=("Segoe UI", 24, "bold")).pack(pady=(22, 4))
        tk.Label(self, text="Build 0.4.21 | Branch 2 | Offline Pronunciation and Safe Android Cleanup | 2026-10-28",
                 font=("Segoe UI", 9), fg="#326a80").pack(pady=(0, 4))
        tk.Label(
            self,
            text="Local speech analysis, pairing, recording, and personalized learning",
            font=("Segoe UI", 10)
        ).pack(pady=(0, 16))

        self.server_status = tk.StringVar(value="Server stopped")
        self.connection_info = tk.StringVar(value=f"Local address: {self.local_ip()}:8000")

        status = tk.LabelFrame(self, text="Status")
        status.pack(fill="x", padx=22, pady=10)
        tk.Label(status, textvariable=self.server_status, font=("Segoe UI", 12, "bold")).pack(pady=(10, 2))
        tk.Label(status, textvariable=self.connection_info, font=("Segoe UI", 10)).pack(pady=(0, 10))

        buttons = tk.Frame(self)
        buttons.pack(fill="x", padx=22, pady=8)

        self._button(buttons, "Start Parent PC", self.start_server, 0, 0)
        self._button(buttons, "Stop Parent PC", self.stop_server, 0, 1)
        self._button(buttons, "Pair Phone", self.pair_phone, 1, 0)
        self._button(buttons, "Direct Recording", self.direct_recording, 1, 1)
        self._button(buttons, "Recording History", self.open_recording_history, 2, 0)
        self._button(buttons, "Check Bluetooth", self.check_bluetooth, 2, 1)
        self._button(buttons, "Open Data Folder", self.open_data_folder, 3, 0)
        self._button(buttons, "Reference Audio Library", self.open_reference_audio, 3, 1)
        self._button(buttons, "Phase 3 Learning History", self.open_learning_history, 4, 0)
        self._button(buttons, "13-Layer Health", self.open_layer_health, 4, 1)
        self._button(buttons, "Open API Diagnostic Logs", self.open_api_logs, 5, 0)
        self._button(buttons, "Check Upload Storage", self.check_upload_storage, 5, 1)

        instructions = tk.LabelFrame(self, text="Quick Start")
        instructions.pack(fill="both", expand=True, padx=22, pady=(8, 18))
        tk.Label(
            instructions,
            justify="left",
            anchor="nw",
            wraplength=550,
            font=("Segoe UI", 10),
            text=(
                "1. Click Start Parent PC.\n"
                "2. Click Pair Phone the first time you connect an Android device.\n"
                "3. On the phone, open Parent PC Connection → Easy Connect.\n"
                "4. Open Recording History to search saved audio directly.\n"
                "5. Use Direct Recording when working one-on-one without the phone.\n\n"
                "Bluetooth is used for pairing and connection setup. "
                "Speech audio and analysis stay on the local Wi-Fi/LAN connection."
            )
        ).pack(fill="both", expand=True, padx=14, pady=14)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _button(self, parent, text, command, row, column):
        tk.Button(parent, text=text, width=22, height=2, command=command).grid(
            row=row, column=column, padx=8, pady=7, sticky="ew"
        )
        parent.columnconfigure(column, weight=1)

    def open_learning_history(self):
        from phase3_learning_gui import LearningHistoryWindow
        LearningHistoryWindow(self)

    def open_layer_health(self):
        from phase3_learning_gui import LayerHealthWindow
        LayerHealthWindow(self)

    def open_reference_audio(self):
        from reference_audio_gui import ReferenceAudioWindow
        ReferenceAudioWindow(self)

    def local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.4)  # Never delay the Parent PC window when offline.
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except OSError:
            return "127.0.0.1"
        finally:
            s.close()

    def open_api_logs(self):
        USER_DATA.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(str(USER_DATA))
        else:
            messagebox.showinfo("API Logs", str(USER_DATA))

    def start_server(self):
        if self.api_proc and self.api_proc.poll() is None:
            write_event("start_ignored_already_running", serverPid=self.api_proc.pid)
            return
        try:
            USER_DATA.mkdir(parents=True, exist_ok=True)
            flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            command = ([sys.executable, "--server"] if FROZEN else
                       [sys.executable, str(API_SCRIPT)])
            # Even failures before Python's logging starts must remain visible.
            console_log = USER_DATA / "parent_pc_server_console.log"
            with console_log.open("ab", buffering=0) as stream:
                self.api_proc = subprocess.Popen(
                    command, cwd=str(ROOT), stdout=stream,
                    stderr=subprocess.STDOUT, creationflags=flags
                )
            self._monitor_generation += 1
            generation = self._monitor_generation
            self._stop_requested = False
            self.server_status.set("Server starting…")
            write_event("server_process_started", serverPid=self.api_proc.pid,
                        frozen=FROZEN, build="phase3_api_diagnostics")
            threading.Thread(target=self._monitor_server,
                             args=(self.api_proc, generation), daemon=True).start()

            if BT_EXE.exists() and (self.bt_proc is None or self.bt_proc.poll() is not None):
                self.bt_proc = subprocess.Popen([str(BT_EXE)], cwd=str(ROOT))
        except Exception as exc:
            write_event("server_spawn_failed", errorType=type(exc).__name__,
                        winerror=getattr(exc, "winerror", None))
            messagebox.showerror("Hearlium Parent PC", str(exc))

    def _set_server_status_safe(self, message):
        try:
            self.after(0, self.server_status.set, message)
        except (RuntimeError, tk.TclError):
            pass  # Window closed during health check.

    def _monitor_server(self, proc, generation):
        """Keep monitoring AFTER ready; capture unexplained API loss at any time."""
        start = time.monotonic()
        timeline = ConnectionTimeline()
        last_display = None
        while generation == self._monitor_generation:
            exit_code = proc.poll()
            if exit_code is not None:
                write_event("server_process_exited", serverPid=proc.pid, exitCode=exit_code,
                            expected=self._stop_requested, uptimeSeconds=round(time.monotonic()-start, 1))
                if not self._stop_requested:
                    self._set_server_status_safe(f"API stopped unexpectedly (exit code {exit_code}) · Open API Diagnostic Logs")
                return

            elapsed = int(time.monotonic() - start)
            state = "offline"
            msg = "API unreachable · check API Diagnostic Logs"
            details = {"serverPid": proc.pid, "elapsedSeconds": elapsed}
            try:
                began = time.monotonic()
                with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=1.5) as response:
                    health = json.loads(response.read(32 * 1024).decode("utf-8"))
                details["responseMs"] = round(1000 * (time.monotonic() - began))
                state, stage = classify_health(health)
                if state == "ready":
                    msg = "Server running · AI models ready · monitoring API"
                elif state == "api_ready":
                    msg = "Server running · API monitored"
                elif state == "initializing":
                    msg = f"Local API listening · {health.get('stage', 'Initializing')} ({elapsed}s)"
                elif state == "model_loading":
                    loading = health.get("modelLoading") or {}
                    msg = f"Server running · {loading.get('stage', stage)} ({elapsed}s)"
                elif state in ("model_error", "partial", "startup_failed"):
                    msg = stage + " · Open API Diagnostic Logs"
                else:
                    msg = "Unexpected API response · Open API Diagnostic Logs"
            except Exception as exc:
                details["errorType"] = type(exc).__name__
                reason = getattr(exc, "reason", None)
                details["reasonType"] = type(reason).__name__ if reason is not None else None
                details["winerror"] = getattr(reason if reason is not None else exc, "winerror", None)
                details["errno"] = getattr(reason if reason is not None else exc, "errno", None)
                if isinstance(exc, urllib.error.HTTPError):
                    details["httpStatus"] = exc.code
                msg = "API connection lost · Open API Diagnostic Logs"

            previous_state = timeline.state
            timeline.observe(state, **details)
            if state == "offline" and previous_state != "offline":
                listener = windows_listener_pid(8000)
                write_event("api_port_snapshot", port=8000,
                            listeningPid=listener, expectedPid=proc.pid,
                            listenerMatchesServer=listener == proc.pid if listener is not None else False)
            if msg != last_display:
                self._set_server_status_safe(msg)
                last_display = msg
            # Stop normally when the window closes; no silent restart or retry
            # of recordings/feedback that could duplicate caregiver decisions.
            time.sleep(3)

    def stop_server(self):
        self._stop_requested = True
        self._monitor_generation += 1
        for proc in (self.bt_proc, self.api_proc):
            try:
                if proc and proc.poll() is None:
                    write_event("stop_requested", serverPid=proc.pid,
                                isApi=proc is self.api_proc)
                    proc.terminate()
            except Exception as exc:
                write_event("stop_request_failed", errorType=type(exc).__name__)
        self.server_status.set("Server stopped")

    def check_upload_storage(self):
        def work():
            try:
                command = ([sys.executable] if FROZEN else
                           [sys.executable, str(ROOT / 'parent_pc_local' / 'hearlium_launcher.py')])
                process = subprocess.run(command + ['--verify-android-retry'],
                                         creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                                         timeout=60)
                if process.returncode:
                    raise RuntimeError('Upload storage check failed; inspect the diagnostic logs.')
                self.after(0, lambda: messagebox.showinfo('Upload storage check',
                    'Synthetic retry and identity-conflict checks passed.\n'
                    'Report: analysis_results/upload_retry_check_0.4.17.json\n'
                    'Actual phone/network checks remain pending.'))
            except Exception as exc:
                self.after(0, lambda text=str(exc): messagebox.showerror('Upload storage check', text))
        threading.Thread(target=work, daemon=True).start()

    def pair_phone(self):
        if not FROZEN and not PAIR_PHONE.exists():
            messagebox.showerror("Pair Phone", "Pair Phone component was not found.")
            return
        self.start_server()
        subprocess.Popen(([sys.executable, "--pair"] if FROZEN else [sys.executable, str(PAIR_PHONE)]), cwd=str(ROOT))

    def direct_recording(self):
        if not FROZEN and not DIRECT_RECORDING.exists():
            messagebox.showerror("Direct Recording", "Direct Recording component was not found.")
            return
        subprocess.Popen(([sys.executable, "--record"] if FROZEN else [sys.executable, str(DIRECT_RECORDING)]), cwd=str(ROOT))

    def open_recording_history(self):
        """Open the SAME protected Recording History tab directly from Home."""
        if not FROZEN and not DIRECT_RECORDING.exists():
            messagebox.showerror("Recording History", "Recording History component was not found.")
            return
        args = ([sys.executable, "--record-history"] if FROZEN else
                [sys.executable, str(DIRECT_RECORDING), "--history"])
        subprocess.Popen(args, cwd=str(ROOT))

    def check_bluetooth(self):
        if BT_EXE.exists():
            messagebox.showinfo("Bluetooth", "Bluetooth pairing helper is installed and ready.")
        else:
            messagebox.showinfo(
                "Bluetooth",
                "The Windows Bluetooth helper is not present in this build yet.\n\n"
                "The installer builder can compile it when the .NET 8 SDK is installed."
            )

    def open_data_folder(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        os.startfile(str(DATA_DIR))

    def on_close(self):
        self.stop_server()
        self.destroy()

if __name__ == "__main__":
    HearliumParentPC().mainloop()
