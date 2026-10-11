from __future__ import annotations

import json
import queue
import threading
import time
import uuid
import wave
from datetime import datetime
from pathlib import Path

import requests
import sounddevice as sd
import tkinter as tk
from tkinter import messagebox, ttk

ROOT = Path(__file__).resolve().parents[1]
RECORDINGS_DIR = ROOT / "parent_pc_local" / "recordings"
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"
API_URL = "http://127.0.0.1:8000"


class DirectRecorder(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hearlium Parent PC Recording")
        self.geometry("720x620")
        self.minsize(680, 560)

        self.audio_queue: queue.Queue[bytes] = queue.Queue()
        self.stream = None
        self.recording = False
        self.start_time = 0.0
        self.timer_job = None
        self.current_file: Path | None = None
        self.last_result: dict | None = None

        self.speaker_id = tk.StringVar(value="student-1")
        self.context = tk.StringVar()
        self.status = tk.StringVar(value="Ready")
        self.timer = tk.StringVar(value="00:00")
        self.file_text = tk.StringVar(value="No recording yet")

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 18, "pady": 8}

        tk.Label(self, text="Hearlium Parent PC Recording",
                 font=("Segoe UI", 22, "bold")).pack(pady=(18, 4))
        tk.Label(self, text="Record directly on the Parent PC for one-on-one sessions.",
                 font=("Segoe UI", 10)).pack(pady=(0, 14))

        info = tk.Frame(self)
        info.pack(fill="x", **pad)

        tk.Label(info, text="Speaker / Student ID:", anchor="w").grid(row=0, column=0, sticky="w")
        tk.Entry(info, textvariable=self.speaker_id, width=32).grid(row=0, column=1, sticky="ew", padx=(10, 0))

        tk.Label(info, text="Optional context:", anchor="w").grid(row=1, column=0, sticky="w", pady=(8, 0))
        tk.Entry(info, textvariable=self.context, width=48).grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(8, 0))
        info.columnconfigure(1, weight=1)

        status_frame = tk.LabelFrame(self, text="Recording status")
        status_frame.pack(fill="x", **pad)
        tk.Label(status_frame, textvariable=self.status, font=("Segoe UI", 13, "bold")).pack(pady=(10, 2))
        tk.Label(status_frame, textvariable=self.timer, font=("Consolas", 20, "bold")).pack(pady=2)
        tk.Label(status_frame, textvariable=self.file_text, wraplength=620).pack(pady=(2, 10))

        controls = tk.Frame(self)
        controls.pack(pady=6)

        self.record_btn = tk.Button(controls, text="Record", width=16, command=self.start_recording)
        self.record_btn.grid(row=0, column=0, padx=6)

        self.stop_btn = tk.Button(controls, text="Stop", width=16, state="disabled", command=self.stop_recording)
        self.stop_btn.grid(row=0, column=1, padx=6)

        self.analyze_btn = tk.Button(controls, text="Analyze Recording", width=18, state="disabled", command=self.analyze_recording)
        self.analyze_btn.grid(row=0, column=2, padx=6)

        result_frame = tk.LabelFrame(self, text="Analysis result")
        result_frame.pack(fill="both", expand=True, **pad)

        self.result_box = tk.Text(result_frame, wrap="word", height=16)
        self.result_box.pack(fill="both", expand=True, padx=10, pady=10)

        bottom = tk.Frame(self)
        bottom.pack(fill="x", padx=18, pady=(0, 16))
        tk.Button(bottom, text="Open Recording Folder", command=self.open_recording_folder).pack(side="left")
        tk.Button(bottom, text="Clear Results", command=self.clear_results).pack(side="right")

    def start_recording(self):
        if self.recording:
            return
        speaker = self.speaker_id.get().strip() or "anonymous"
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in speaker)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_file = RECORDINGS_DIR / f"{safe}_{stamp}.wav"

        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

        try:
            self.stream = sd.RawInputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                callback=self._audio_callback
            )
            self.stream.start()
        except Exception as exc:
            self.stream = None
            messagebox.showerror("Microphone error", f"Could not start the microphone.\n\n{exc}")
            return

        self.recording = True
        self.start_time = time.monotonic()
        self.status.set("● Recording")
        self.timer.set("00:00")
        self.record_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.analyze_btn.config(state="disabled")
        self._update_timer()

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            pass
        if self.recording:
            self.audio_queue.put(bytes(indata))

    def _update_timer(self):
        if not self.recording:
            return
        elapsed = int(time.monotonic() - self.start_time)
        self.timer.set(f"{elapsed // 60:02d}:{elapsed % 60:02d}")
        self.timer_job = self.after(250, self._update_timer)

    def stop_recording(self):
        if not self.recording:
            return
        self.recording = False
        if self.timer_job:
            try:
                self.after_cancel(self.timer_job)
            except Exception:
                pass
            self.timer_job = None

        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
        finally:
            self.stream = None

        chunks = []
        while not self.audio_queue.empty():
            try:
                chunks.append(self.audio_queue.get_nowait())
            except queue.Empty:
                break

        if not chunks or self.current_file is None:
            self.status.set("No audio captured")
            self.record_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            return

        with wave.open(str(self.current_file), "wb") as wav:
            wav.setnchannels(CHANNELS)
            wav.setsampwidth(2)
            wav.setframerate(SAMPLE_RATE)
            wav.writeframes(b"".join(chunks))

        elapsed = int(time.monotonic() - self.start_time)
        self.status.set("Recording saved")
        self.timer.set(f"{elapsed // 60:02d}:{elapsed % 60:02d}")
        self.file_text.set(str(self.current_file))
        self.record_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.analyze_btn.config(state="normal")

    def analyze_recording(self):
        if not self.current_file or not self.current_file.exists():
            messagebox.showinfo("Analyze Recording", "Record a speech sample first.")
            return

        self.analyze_btn.config(state="disabled")
        self.status.set("Analyzing…")
        threading.Thread(target=self._analyze_worker, daemon=True).start()

    def _analyze_worker(self):
        speaker = self.speaker_id.get().strip() or "anonymous"
        context = self.context.get().strip()
        session_id = str(uuid.uuid4())
        recording_id = self.current_file.stem if self.current_file else str(uuid.uuid4())

        try:
            with self.current_file.open("rb") as f:
                response = requests.post(
                    f"{API_URL}/v1/analyze-audio",
                    files={"audio": (self.current_file.name, f, "audio/wav")},
                    data={
                        "context": context,
                        "speaker_id": speaker,
                        "session_id": session_id,
                        "recording_id": recording_id
                    },
                    timeout=180
                )
            response.raise_for_status()
            result = response.json()
            self.last_result = result
            self.after(0, self._show_result, result)
        except Exception as exc:
            self.after(0, self._show_error, str(exc))

    def _show_result(self, result: dict):
        self.status.set("Analysis complete")
        self.analyze_btn.config(state="normal")

        observed = result.get("observed") or result.get("observation") or {}
        interpretation = result.get("interpretation") or {}
        candidates = result.get("candidates") or interpretation.get("candidates") or []

        lines = []
        if isinstance(observed, dict):
            phonemes = observed.get("phonemes") or observed.get("ipa") or observed.get("observedIpa")
            if phonemes:
                lines.append(f"Observed phonemes: {phonemes}")
        elif observed:
            lines.append(f"Observed: {observed}")

        if isinstance(candidates, list) and candidates:
            lines.append("\nTop candidate meanings:")
            for i, item in enumerate(candidates[:5], 1):
                if isinstance(item, dict):
                    word = item.get("word") or item.get("candidate") or item.get("text") or str(item)
                    score = item.get("score") or item.get("confidence")
                    if isinstance(score, (int, float)):
                        lines.append(f"{i}. {word}  ({score:.3f})")
                    else:
                        lines.append(f"{i}. {word}")
                else:
                    lines.append(f"{i}. {item}")

        if not lines:
            lines.append(json.dumps(result, indent=2))

        self.result_box.delete("1.0", "end")
        self.result_box.insert("1.0", "\n".join(lines))

    def _show_error(self, msg: str):
        self.status.set("Analysis failed")
        self.analyze_btn.config(state="normal")
        messagebox.showerror(
            "Analysis failed",
            "Could not analyze the recording.\n\n"
            "Make sure the Parent PC local backend is running.\n\n"
            f"{msg}"
        )

    def open_recording_folder(self):
        import os
        os.startfile(str(RECORDINGS_DIR))

    def clear_results(self):
        self.result_box.delete("1.0", "end")

    def on_close(self):
        if self.recording:
            self.stop_recording()
        self.destroy()


if __name__ == "__main__":
    app = DirectRecorder()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
