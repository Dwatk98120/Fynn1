from __future__ import annotations

import json
import os
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
from tkinter import messagebox, simpledialog, ttk

ROOT = Path(__file__).resolve().parents[1]
RECORDINGS_DIR = ROOT / "parent_pc_local" / "recordings"
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"
API_URL = "http://127.0.0.1:8000"


def _metadata_path(wav_path: Path) -> Path:
    return wav_path.with_suffix(".json")


def _load_metadata(wav_path: Path) -> dict:
    p = _metadata_path(wav_path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_metadata(wav_path: Path, data: dict) -> None:
    p = _metadata_path(wav_path)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)


class DirectRecorder(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hearlium Parent PC Recording")
        self.geometry("900x720")
        self.minsize(820, 660)

        self.audio_queue: queue.Queue[bytes] = queue.Queue()
        self.stream = None
        self.recording = False
        self.start_time = 0.0
        self.timer_job = None
        self.current_file: Path | None = None
        self.last_result: dict | None = None

        self.speaker_id = tk.StringVar(value="student-1")
        self.context = tk.StringVar()
        self.notes = tk.StringVar()
        self.confirmed_word = tk.StringVar()
        self.status = tk.StringVar(value="Ready")
        self.timer = tk.StringVar(value="00:00")
        self.file_text = tk.StringVar(value="No recording yet")
        self.approval_status = tk.StringVar(value="Not reviewed")

        self._build_ui()
        self.refresh_history()

    def _build_ui(self):
        tk.Label(self, text="Hearlium Parent PC Recording",
                 font=("Segoe UI", 22, "bold")).pack(pady=(16, 3))
        tk.Label(
            self,
            text="Record, analyze, review, and approve speech examples for learning.",
            font=("Segoe UI", 10)
        ).pack(pady=(0, 10))

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=14, pady=(4, 12))

        self.record_tab = tk.Frame(notebook)
        self.history_tab = tk.Frame(notebook)
        notebook.add(self.record_tab, text="Record & Analyze")
        notebook.add(self.history_tab, text="Recording History")

        self._build_record_tab(self.record_tab)
        self._build_history_tab(self.history_tab)

    def _build_record_tab(self, parent):
        info = tk.Frame(parent)
        info.pack(fill="x", padx=18, pady=10)

        tk.Label(info, text="Speaker / Student ID:", anchor="w").grid(row=0, column=0, sticky="w")
        tk.Entry(info, textvariable=self.speaker_id, width=32).grid(row=0, column=1, sticky="ew", padx=(10, 0))

        tk.Label(info, text="Optional context:", anchor="w").grid(row=1, column=0, sticky="w", pady=(8, 0))
        tk.Entry(info, textvariable=self.context, width=48).grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(8, 0))

        tk.Label(info, text="Caregiver / teacher notes:", anchor="w").grid(row=2, column=0, sticky="w", pady=(8, 0))
        tk.Entry(info, textvariable=self.notes, width=48).grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=(8, 0))
        info.columnconfigure(1, weight=1)

        status_frame = tk.LabelFrame(parent, text="Recording status")
        status_frame.pack(fill="x", padx=18, pady=6)
        tk.Label(status_frame, textvariable=self.status, font=("Segoe UI", 12, "bold")).pack(pady=(8, 2))
        tk.Label(status_frame, textvariable=self.timer, font=("Consolas", 18, "bold")).pack(pady=2)
        tk.Label(status_frame, textvariable=self.file_text, wraplength=760).pack(pady=(2, 8))

        controls = tk.Frame(parent)
        controls.pack(pady=6)

        self.record_btn = tk.Button(controls, text="Record", width=15, command=self.start_recording)
        self.record_btn.grid(row=0, column=0, padx=5)
        self.stop_btn = tk.Button(controls, text="Stop", width=15, state="disabled", command=self.stop_recording)
        self.stop_btn.grid(row=0, column=1, padx=5)
        self.analyze_btn = tk.Button(controls, text="Analyze Recording", width=18, state="disabled", command=self.analyze_recording)
        self.analyze_btn.grid(row=0, column=2, padx=5)
        self.play_btn = tk.Button(controls, text="Play Recording", width=16, state="disabled", command=self.play_current)
        self.play_btn.grid(row=0, column=3, padx=5)

        result_frame = tk.LabelFrame(parent, text="Analysis result")
        result_frame.pack(fill="both", expand=True, padx=18, pady=8)
        self.result_box = tk.Text(result_frame, wrap="word", height=13)
        self.result_box.pack(fill="both", expand=True, padx=10, pady=10)

        review = tk.LabelFrame(parent, text="Caregiver review")
        review.pack(fill="x", padx=18, pady=(2, 10))

        tk.Label(review, text="Confirmed / corrected word:").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 6))
        tk.Entry(review, textvariable=self.confirmed_word, width=28).grid(row=0, column=1, sticky="w", padx=6, pady=(10, 6))
        tk.Label(review, textvariable=self.approval_status, font=("Segoe UI", 10, "bold")).grid(row=0, column=2, sticky="w", padx=12, pady=(10, 6))

        tk.Button(review, text="Approve for Learning", command=self.approve_for_learning, width=20).grid(
            row=1, column=0, padx=10, pady=(0, 10)
        )
        tk.Button(review, text="Save Correction Only", command=self.save_correction_only, width=20).grid(
            row=1, column=1, padx=6, pady=(0, 10)
        )
        tk.Button(review, text="Reject Interpretation", command=self.reject_interpretation, width=20).grid(
            row=1, column=2, padx=6, pady=(0, 10)
        )

        bottom = tk.Frame(parent)
        bottom.pack(fill="x", padx=18, pady=(0, 12))
        tk.Button(bottom, text="Open Recording Folder", command=self.open_recording_folder).pack(side="left")
        tk.Button(bottom, text="Clear Results", command=self.clear_results).pack(side="right")

    def _build_history_tab(self, parent):
        top = tk.Frame(parent)
        top.pack(fill="x", padx=12, pady=10)
        tk.Button(top, text="Refresh", command=self.refresh_history).pack(side="left")
        tk.Button(top, text="Play", command=self.play_selected_history).pack(side="left", padx=5)
        tk.Button(top, text="Reanalyze", command=self.reanalyze_selected).pack(side="left", padx=5)
        tk.Button(top, text="Load into Review", command=self.load_selected_into_review).pack(side="left", padx=5)
        tk.Button(top, text="Delete", command=self.delete_selected_history).pack(side="right")

        columns = ("date", "speaker", "status", "word", "file")
        self.history = ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse")
        for col, width in [("date", 145), ("speaker", 120), ("status", 120), ("word", 120), ("file", 300)]:
            self.history.heading(col, text=col.title())
            self.history.column(col, width=width, anchor="w")
        self.history.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        notes_frame = tk.LabelFrame(parent, text="Selected recording details")
        notes_frame.pack(fill="x", padx=12, pady=(0, 12))
        self.history_details = tk.Text(notes_frame, height=8, wrap="word")
        self.history_details.pack(fill="x", padx=8, pady=8)
        self.history.bind("<<TreeviewSelect>>", lambda _e: self.show_history_details())

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
        self.approval_status.set("Not reviewed")
        self.confirmed_word.set("")
        self.record_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.analyze_btn.config(state="disabled")
        self.play_btn.config(state="disabled")
        self._update_timer()

    def _audio_callback(self, indata, frames, time_info, status):
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
        meta = {
            "speakerId": self.speaker_id.get().strip() or "anonymous",
            "context": self.context.get().strip(),
            "notes": self.notes.get().strip(),
            "createdAt": datetime.now().isoformat(timespec="seconds"),
            "durationSeconds": elapsed,
            "reviewStatus": "not_reviewed",
            "recordingFile": self.current_file.name,
        }
        _save_metadata(self.current_file, meta)

        self.status.set("Recording saved")
        self.timer.set(f"{elapsed // 60:02d}:{elapsed % 60:02d}")
        self.file_text.set(str(self.current_file))
        self.record_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.analyze_btn.config(state="normal")
        self.play_btn.config(state="normal")
        self.refresh_history()

    def analyze_recording(self):
        if not self.current_file or not self.current_file.exists():
            messagebox.showinfo("Analyze Recording", "Record or load a speech sample first.")
            return
        self.analyze_btn.config(state="disabled")
        self.status.set("Analyzing…")
        threading.Thread(target=self._analyze_worker, args=(self.current_file,), daemon=True).start()

    def _analyze_worker(self, wav_path: Path):
        meta = _load_metadata(wav_path)
        speaker = (meta.get("speakerId") or self.speaker_id.get().strip() or "anonymous")
        context = meta.get("context") if "context" in meta else self.context.get().strip()
        session_id = str(uuid.uuid4())
        recording_id = wav_path.stem

        try:
            with wav_path.open("rb") as f:
                response = requests.post(
                    f"{API_URL}/v1/analyze-audio",
                    files={"audio": (wav_path.name, f, "audio/wav")},
                    data={
                        "context": context or "",
                        "speaker_id": speaker,
                        "session_id": session_id,
                        "recording_id": recording_id
                    },
                    timeout=180
                )
            response.raise_for_status()
            result = response.json()

            observation = result.get("observation") or {}
            observation_id = observation.get("observationId") if isinstance(observation, dict) else None
            candidates = result.get("candidates") or []
            best_word = ""
            if candidates and isinstance(candidates[0], dict):
                best_word = str(candidates[0].get("word") or candidates[0].get("candidate") or "")

            meta.update({
                "speakerId": speaker,
                "context": context or "",
                "analysisResult": result,
                "observationId": observation_id or "",
                "recordingId": result.get("recordingId") or recording_id,
                "sessionId": result.get("sessionId") or session_id,
                "bestCandidate": best_word,
                "analyzedAt": datetime.now().isoformat(timespec="seconds"),
            })
            _save_metadata(wav_path, meta)

            self.last_result = result
            self.current_file = wav_path
            self.after(0, self._show_result, result)
            self.after(0, self.refresh_history)
        except Exception as exc:
            self.after(0, self._show_error, str(exc))

    def _show_result(self, result: dict):
        self.status.set("Analysis complete")
        self.analyze_btn.config(state="normal")
        self.play_btn.config(state="normal")

        observation = result.get("observation") or {}
        candidates = result.get("candidates") or []

        lines = []
        if isinstance(observation, dict):
            phonemes = observation.get("observedPhonemes") or observation.get("phonemes") or observation.get("ipa")
            transcript = observation.get("transcript")
            if transcript:
                lines.append(f"Observed speech: {transcript}")
            if phonemes:
                lines.append(f"Observed phonemes: {phonemes}")

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

        quality = result.get("recordingQuality") or {}
        if isinstance(quality, dict) and quality:
            score = quality.get("score")
            label = quality.get("label", "")
            usable = quality.get("usable")
            if isinstance(score, (int, float)):
                lines.append(f"\nRecording quality: {int(score * 100)}% ({label})")
            if usable is False:
                issues = quality.get("issues") or []
                if issues:
                    lines.append("Quality issues: " + ", ".join(str(x).replace("_", " ") for x in issues))

        phoneme_analysis = result.get("phonemeAnalysis") or {}
        if isinstance(phoneme_analysis, dict) and phoneme_analysis:
            confidence = phoneme_analysis.get("overallPhonemeConfidence")
            band = phoneme_analysis.get("confidenceBand", "")
            if isinstance(confidence, (int, float)):
                lines.append(f"\nPhoneme confidence: {int(confidence * 100)}% ({str(band).replace('_',' ')})")
            uncertain = phoneme_analysis.get("uncertainOrDistorted") or []
            if uncertain:
                lines.append("Uncertain / distorted sounds:")
                for item in uncertain:
                    if isinstance(item, dict):
                        phone=item.get("phoneme","?"); c=item.get("confidence"); clarity=str(item.get("clarity","uncertain")).replace("_"," ")
                        lines.append(f"• /{phone}/ — {int(c*100)}% ({clarity})" if isinstance(c,(int,float)) else f"• /{phone}/ — {clarity}")

        comparison = result.get("phonemeComparison") or {}
        if isinstance(comparison, dict) and comparison:
            substitutions = comparison.get("substitutions") or []
            deletions = comparison.get("deletions") or []
            insertions = comparison.get("insertions") or []

            if substitutions:
                lines.append("\nChanged sounds:")
                for item in substitutions:
                    if isinstance(item, dict):
                        conf = item.get("observedConfidence")
                        suffix = f" — {int(conf * 100)}% sound confidence" if isinstance(conf, (int, float)) else ""
                        lines.append(
                            f"• /{item.get('expected','?')}/ → /{item.get('observed','?')}/ "
                            f"({item.get('position','unknown')}){suffix}"
                        )
            if deletions:
                lines.append("\nDropped sounds:")
                for item in deletions:
                    if isinstance(item, dict):
                        lines.append(
                            f"• /{item.get('expected','?')}/ dropped "
                            f"({item.get('position','unknown')})"
                        )
            if insertions:
                lines.append("\nInserted sounds:")
                for item in insertions:
                    if isinstance(item, dict):
                        lines.append(f"• extra /{item.get('observed','?')}/")

        if not lines:
            lines.append(json.dumps(result, indent=2))

        if isinstance(candidates, list) and candidates and isinstance(candidates[0], dict):
            self.confirmed_word.set(
                str(candidates[0].get("word") or candidates[0].get("candidate") or "")
            )

        self.result_box.delete("1.0", "end")
        self.result_box.insert("1.0", "\n".join(lines))

        if self.current_file:
            meta = _load_metadata(self.current_file)
            self.approval_status.set(meta.get("reviewStatus", "Not reviewed").replace("_", " ").title())

    def _feedback_payload(self, approved: bool, correction_only: bool = False):
        if not self.current_file:
            raise ValueError("No recording is loaded.")
        meta = _load_metadata(self.current_file)
        observation_id = str(meta.get("observationId") or "").strip()
        if not observation_id:
            raise ValueError("Analyze this recording before submitting caregiver feedback.")

        word = self.confirmed_word.get().strip()
        if not word and approved:
            raise ValueError("Enter the confirmed or corrected word before approving it for learning.")

        return meta, {
            "observation_id": observation_id,
            "speaker_id": str(meta.get("speakerId") or self.speaker_id.get().strip() or "anonymous"),
            "recording_id": str(meta.get("recordingId") or self.current_file.stem),
            "confirmed_word": "" if correction_only else word,
            "corrected_word": word if correction_only else "",
            "approved_for_learning": "true" if approved else "false",
        }

    def approve_for_learning(self):
        self._submit_feedback(review_status="approved_for_learning", approved=True, correction_only=False)

    def save_correction_only(self):
        self._submit_feedback(review_status="corrected_not_approved", approved=False, correction_only=True)

    def reject_interpretation(self):
        if not self.current_file:
            messagebox.showinfo("Review", "Load or analyze a recording first.")
            return
        meta = _load_metadata(self.current_file)
        meta["reviewStatus"] = "rejected"
        meta["reviewedAt"] = datetime.now().isoformat(timespec="seconds")
        meta["confirmedWord"] = self.confirmed_word.get().strip()
        meta["notes"] = self.notes.get().strip() or meta.get("notes", "")
        _save_metadata(self.current_file, meta)
        self.approval_status.set("Rejected")
        self.refresh_history()
        messagebox.showinfo(
            "Interpretation rejected",
            "The interpretation was marked rejected. It was not approved for learning."
        )

    def _submit_feedback(self, review_status: str, approved: bool, correction_only: bool):
        try:
            meta, payload = self._feedback_payload(approved, correction_only)
        except ValueError as exc:
            messagebox.showinfo("Caregiver Review", str(exc))
            return

        self.status.set("Saving caregiver feedback…")

        def worker():
            try:
                response = requests.post(
                    f"{API_URL}/v1/learning/feedback",
                    data=payload,
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()

                meta["reviewStatus"] = review_status
                meta["reviewedAt"] = datetime.now().isoformat(timespec="seconds")
                meta["confirmedWord"] = self.confirmed_word.get().strip()
                meta["notes"] = self.notes.get().strip() or meta.get("notes", "")
                meta["learningFeedback"] = result
                _save_metadata(self.current_file, meta)

                self.after(0, lambda: self.status.set("Caregiver feedback saved"))
                self.after(0, lambda: self.approval_status.set(review_status.replace("_", " ").title()))
                self.after(0, self.refresh_history)
                self.after(0, lambda: messagebox.showinfo(
                    "Caregiver Review",
                    "Approved for learning." if approved else "Correction saved without approving it for learning."
                ))
            except Exception as exc:
                self.after(0, lambda: self._show_error(f"Feedback could not be saved: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def refresh_history(self):
        if not hasattr(self, "history"):
            return
        for item in self.history.get_children():
            self.history.delete(item)

        wavs = sorted(RECORDINGS_DIR.glob("*.wav"), key=lambda p: p.stat().st_mtime, reverse=True)
        for wav_path in wavs:
            meta = _load_metadata(wav_path)
            created = meta.get("createdAt") or datetime.fromtimestamp(wav_path.stat().st_mtime).isoformat(timespec="minutes")
            speaker = meta.get("speakerId", "")
            status = meta.get("reviewStatus", "not_reviewed").replace("_", " ")
            word = meta.get("confirmedWord") or meta.get("bestCandidate") or ""
            self.history.insert(
                "", "end", iid=str(wav_path),
                values=(created, speaker, status, word, wav_path.name)
            )

    def _selected_history_path(self) -> Path | None:
        selected = self.history.selection()
        if not selected:
            messagebox.showinfo("Recording History", "Select a recording first.")
            return None
        return Path(selected[0])

    def show_history_details(self):
        wav_path = self._selected_history_path_silent()
        if not wav_path:
            return
        meta = _load_metadata(wav_path)
        details = {
            "file": wav_path.name,
            "speakerId": meta.get("speakerId"),
            "createdAt": meta.get("createdAt"),
            "context": meta.get("context"),
            "notes": meta.get("notes"),
            "reviewStatus": meta.get("reviewStatus"),
            "confirmedWord": meta.get("confirmedWord"),
            "bestCandidate": meta.get("bestCandidate"),
            "observationId": meta.get("observationId"),
        }
        self.history_details.delete("1.0", "end")
        self.history_details.insert("1.0", json.dumps(details, indent=2, ensure_ascii=False))

    def _selected_history_path_silent(self) -> Path | None:
        selected = self.history.selection()
        return Path(selected[0]) if selected else None

    def play_current(self):
        if not self.current_file:
            messagebox.showinfo("Playback", "No recording is loaded.")
            return
        self._play_wav(self.current_file)

    def play_selected_history(self):
        wav_path = self._selected_history_path()
        if wav_path:
            self._play_wav(wav_path)

    def _play_wav(self, wav_path: Path):
        if not wav_path.exists():
            messagebox.showerror("Playback", "Recording file was not found.")
            return
        try:
            import winsound
            winsound.PlaySound(str(wav_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as exc:
            messagebox.showerror("Playback", str(exc))

    def reanalyze_selected(self):
        wav_path = self._selected_history_path()
        if not wav_path:
            return
        self.current_file = wav_path
        meta = _load_metadata(wav_path)
        self.speaker_id.set(meta.get("speakerId", "student-1"))
        self.context.set(meta.get("context", ""))
        self.notes.set(meta.get("notes", ""))
        self.file_text.set(str(wav_path))
        self.status.set("Reanalyzing…")
        threading.Thread(target=self._analyze_worker, args=(wav_path,), daemon=True).start()

    def load_selected_into_review(self):
        wav_path = self._selected_history_path()
        if not wav_path:
            return
        meta = _load_metadata(wav_path)
        self.current_file = wav_path
        self.speaker_id.set(meta.get("speakerId", "student-1"))
        self.context.set(meta.get("context", ""))
        self.notes.set(meta.get("notes", ""))
        self.confirmed_word.set(meta.get("confirmedWord") or meta.get("bestCandidate") or "")
        self.file_text.set(str(wav_path))
        self.approval_status.set(meta.get("reviewStatus", "not_reviewed").replace("_", " ").title())
        result = meta.get("analysisResult")
        if isinstance(result, dict):
            self.last_result = result
            self._show_result(result)
        else:
            self.result_box.delete("1.0", "end")
            self.result_box.insert("1.0", "No saved analysis result. Click Analyze Recording.")
        self.analyze_btn.config(state="normal")
        self.play_btn.config(state="normal")

    def delete_selected_history(self):
        wav_path = self._selected_history_path()
        if not wav_path:
            return
        if not messagebox.askyesno("Delete Recording", f"Delete {wav_path.name} and its local review metadata?"):
            return
        try:
            if self.current_file == wav_path:
                self.current_file = None
                self.last_result = None
                self.file_text.set("No recording yet")
                self.result_box.delete("1.0", "end")
                self.approval_status.set("Not reviewed")
            wav_path.unlink(missing_ok=True)
            _metadata_path(wav_path).unlink(missing_ok=True)
            self.refresh_history()
        except Exception as exc:
            messagebox.showerror("Delete Recording", str(exc))

    def _show_error(self, msg: str):
        self.status.set("Operation failed")
        self.analyze_btn.config(state="normal")
        messagebox.showerror("Hearlium Parent PC", msg)

    def open_recording_folder(self):
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
