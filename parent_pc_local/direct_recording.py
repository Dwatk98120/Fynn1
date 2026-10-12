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
from tkinter import filedialog, messagebox, simpledialog, ttk

ROOT = Path(__file__).resolve().parents[1]
RECORDINGS_DIR = ROOT / "parent_pc_local" / "recordings"
ANALYSIS_RESULTS_DIR = ROOT / "parent_pc_local" / "analysis_results"
CONFIG_PATH = ROOT / "parent_pc_local" / "parent_pc_config.json"
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"
DEFAULT_API_URL = "http://127.0.0.1:8000"



def _load_parent_pc_config() -> dict:
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_parent_pc_config(data: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _safe_analysis_filename(wav_path: Path) -> Path:
    return ANALYSIS_RESULTS_DIR / f"{wav_path.stem}_analysis.json"


def _write_analysis_export(wav_path: Path, result: dict) -> Path:
    out = _safe_analysis_filename(wav_path)
    payload = dict(result)
    payload["_parent_pc"] = {
        "file": str(wav_path),
        "api_url": payload.get("_api_url", ""),
        "saved_at": datetime.now().isoformat(timespec="seconds"),
    }
    payload.pop("_api_url", None)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out

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
        self.last_analysis_export: Path | None = None
        self.batch_running = False

        config = _load_parent_pc_config()
        self.api_url = tk.StringVar(value=str(config.get("api_url") or DEFAULT_API_URL))

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
        self.dashboard_tab = tk.Frame(notebook)
        self.evidence_tab = tk.Frame(notebook)
        self.analytics_tab = tk.Frame(notebook)
        self.raw_tab = tk.Frame(notebook)
        self.connection_tab = tk.Frame(notebook)

        notebook.add(self.record_tab, text="Record & Analyze")
        notebook.add(self.history_tab, text="Recording History")
        notebook.add(self.dashboard_tab, text="AI Dashboard")
        notebook.add(self.evidence_tab, text="Evidence")
        notebook.add(self.analytics_tab, text="Analytics & Batch")
        notebook.add(self.raw_tab, text="Raw JSON")
        notebook.add(self.connection_tab, text="Connection")

        self._build_record_tab(self.record_tab)
        self._build_history_tab(self.history_tab)
        self._build_dashboard_tab(self.dashboard_tab)
        self._build_evidence_tab(self.evidence_tab)
        self._build_analytics_tab(self.analytics_tab)
        self._build_raw_tab(self.raw_tab)
        self._build_connection_tab(self.connection_tab)

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


    def _build_dashboard_tab(self, parent):
        toolbar = tk.Frame(parent)
        toolbar.pack(fill="x", padx=12, pady=10)
        tk.Button(toolbar, text="Refresh from Current Result", command=self.refresh_dashboard).pack(side="left")
        tk.Button(toolbar, text="Rebuild Analytics", command=self.rebuild_analytics).pack(side="left", padx=6)

        self.dashboard_box = tk.Text(parent, wrap="word")
        self.dashboard_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.dashboard_box.insert("1.0", "Analyze or load a recording to populate the AI Dashboard.")

    def _build_evidence_tab(self, parent):
        toolbar = tk.Frame(parent)
        toolbar.pack(fill="x", padx=12, pady=10)
        tk.Button(toolbar, text="Refresh Evidence", command=self.refresh_evidence).pack(side="left")

        self.evidence_box = tk.Text(parent, wrap="word")
        self.evidence_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.evidence_box.insert(
            "1.0",
            "Evidence will appear here after analysis.\n\n"
            "The original observation remains immutable; evidence and interpretation are layered on top."
        )

    def _build_analytics_tab(self, parent):
        controls = tk.Frame(parent)
        controls.pack(fill="x", padx=12, pady=10)
        tk.Button(controls, text="Batch Folder", command=self.choose_batch_folder).pack(side="left")
        tk.Button(controls, text="Rebuild Analytics", command=self.rebuild_analytics).pack(side="left", padx=6)
        tk.Button(controls, text="Open Analysis Results", command=self.open_analysis_results_folder).pack(side="left", padx=6)

        self.analytics_box = tk.Text(parent, wrap="word")
        self.analytics_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.analytics_box.insert("1.0", "No analytics have been built yet.")

    def _build_raw_tab(self, parent):
        toolbar = tk.Frame(parent)
        toolbar.pack(fill="x", padx=12, pady=10)
        tk.Button(toolbar, text="Refresh Raw JSON", command=self.refresh_raw_json).pack(side="left")
        self.raw_json_box = tk.Text(parent, wrap="none")
        self.raw_json_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.raw_json_box.insert("1.0", "Raw analysis JSON will appear here.")

    def _build_connection_tab(self, parent):
        frame = tk.LabelFrame(parent, text="Parent PC Local API")
        frame.pack(fill="x", padx=18, pady=18)

        tk.Label(frame, text="API URL:").grid(row=0, column=0, sticky="w", padx=10, pady=12)
        tk.Entry(frame, textvariable=self.api_url, width=52).grid(row=0, column=1, sticky="ew", padx=6, pady=12)
        tk.Button(frame, text="Test Connection", command=self.test_api_connection).grid(row=0, column=2, padx=6, pady=12)
        tk.Button(frame, text="Save", command=self.save_api_url).grid(row=0, column=3, padx=(0, 10), pady=12)
        frame.columnconfigure(1, weight=1)

        tk.Label(
            parent,
            text=(
                "Normal use should stay on the local Parent PC address discovered by pairing. "
                "This manual setting is retained as a diagnostic/fallback control."
            ),
            wraplength=760,
            justify="left"
        ).pack(fill="x", padx=24, pady=(0, 12))

        self.connection_status = tk.StringVar(value="Not tested")
        tk.Label(parent, textvariable=self.connection_status, font=("Segoe UI", 11, "bold")).pack(
            fill="x", padx=24, pady=8
        )

    def api_base(self) -> str:
        value = self.api_url.get().strip().rstrip("/")
        return value or DEFAULT_API_URL

    def save_api_url(self):
        _save_parent_pc_config({"api_url": self.api_base()})
        self.connection_status.set("API URL saved")

    def test_api_connection(self):
        self.connection_status.set("Testing Parent PC Local API…")

        def worker():
            try:
                response = requests.get(f"{self.api_base()}/health", timeout=20)
                response.raise_for_status()
                data = response.json()
                msg = (
                    f"Connected • API {data.get('apiVersion','')} • "
                    f"model={data.get('model','')} • device={data.get('device','')}"
                )
                self.after(0, lambda: self.connection_status.set(msg))
            except Exception as exc:
                self.after(0, lambda: self.connection_status.set(f"Connection failed: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def refresh_dashboard(self):
        result = self.last_result
        if not isinstance(result, dict):
            self.dashboard_box.delete("1.0", "end")
            self.dashboard_box.insert("1.0", "Analyze or load a recording to populate the AI Dashboard.")
            return

        analysis = result.get("analysis") or {}
        candidates = result.get("candidates") or []
        lines = [
            f"TRANSCRIPT: {result.get('transcript', '—')}",
            f"OVERALL CONFIDENCE: {analysis.get('overallConfidence', '—')}",
            f"UNCERTAINTY: {analysis.get('uncertaintyBand', '—')}",
            f"FINAL-CONSONANT PATTERN: {analysis.get('possibleFinalConsonantOmission', False)}",
            f"INITIAL-CONSONANT PATTERN: {analysis.get('possibleInitialConsonantOmission', False)}",
            "",
            "TOP CANDIDATES",
        ]
        for i, candidate in enumerate(candidates[:8], 1):
            if not isinstance(candidate, dict):
                continue
            lines.append(
                f"{i}. {candidate.get('word', candidate.get('candidate', ''))}   "
                f"confidence={candidate.get('confidence', candidate.get('score', ''))}   "
                f"{candidate.get('pattern', '')}"
            )
            lines.append(
                f"   expected={candidate.get('expectedPhonemes','')}   "
                f"observed={candidate.get('observedPhonemes','')}"
            )
            if candidate.get("reason"):
                lines.append(f"   reason={candidate.get('reason')}")
        if self.last_analysis_export:
            lines.extend(["", "Saved analysis:", str(self.last_analysis_export)])

        self.dashboard_box.delete("1.0", "end")
        self.dashboard_box.insert("1.0", "\n".join(lines))

    def refresh_evidence(self):
        result = self.last_result
        if not isinstance(result, dict):
            return

        analysis = result.get("analysis") or {}
        evidence = analysis.get("evidence") or {}
        acoustic = evidence.get("acoustic") or {}
        temporal = evidence.get("temporal") or {}
        observation = result.get("observation") or {}
        phoneme = result.get("phonemeAnalysis") or {}
        learning = analysis.get("learningLayers") or {}

        lines = [
            "IMMUTABLE OBSERVATION",
            f"Observation ID: {observation.get('observationId','—')}",
            f"Observed transcript: {observation.get('transcript', result.get('transcript','—'))}",
            "RULE: interpretation and learning may annotate this observation but cannot rewrite it.",
            "",
            "PHONEME EVIDENCE",
            f"Overall phoneme confidence: {phoneme.get('overallPhonemeConfidence','—')}",
            f"Confidence band: {phoneme.get('confidenceBand','—')}",
            f"Uncertain/distorted count: {phoneme.get('uncertainCount','—')}",
            "",
            "ACOUSTIC EVIDENCE",
            f"RMS: {acoustic.get('rms','—')}",
            f"Final energy ratio: {acoustic.get('finalEnergyRatio','—')}",
            f"Final silence ratio: {acoustic.get('finalSilenceRatio','—')}",
            f"Peak ratio: {acoustic.get('peakRatio','—')}",
            "",
            "TEMPORAL EVIDENCE",
            f"Tail change: {temporal.get('tailChange','—')}",
            f"Tail window: {temporal.get('tailWindowMs','—')} ms",
            "",
            "CANDIDATE EVIDENCE",
        ]

        for candidate in (result.get("candidates") or [])[:8]:
            if isinstance(candidate, dict):
                lines.append(
                    f"{candidate.get('word', candidate.get('candidate',''))}: "
                    f"{json.dumps(candidate.get('evidence',{}), ensure_ascii=False)}"
                )

        lines.extend([
            "",
            "LEARNING LAYERS",
            f"9 Human feedback: {(learning.get('9_humanFeedback') or {}).get('status','—')}",
            f"10 Speaker adaptation: {(learning.get('10_speakerAdaptation') or {}).get('adaptationBoost','—')}",
            f"11 Pattern learning ready: {(learning.get('11_patternLearning') or {}).get('learningReady','—')}",
            f"12 Best next strategy: {(learning.get('12_strategyLearning') or {}).get('bestNextStrategy','—')}",
            f"13 Self-evaluation accuracy: {(learning.get('13_selfEvaluation') or {}).get('accuracy','—')}",
        ])

        self.evidence_box.delete("1.0", "end")
        self.evidence_box.insert("1.0", "\n".join(lines))

    def refresh_raw_json(self):
        self.raw_json_box.delete("1.0", "end")
        if isinstance(self.last_result, dict):
            self.raw_json_box.insert("1.0", json.dumps(self.last_result, indent=2, ensure_ascii=False))
        else:
            self.raw_json_box.insert("1.0", "Raw analysis JSON will appear here.")

    def rebuild_analytics(self):
        total = 0
        final_omission = 0
        initial_omission = 0
        approved = 0
        rejected = 0
        corrected = 0
        words: dict[str, int] = {}
        changed: dict[str, int] = {}
        dropped: dict[str, int] = {}

        seen_keys = set()

        def consume(result: dict, review_status: str = ""):
            nonlocal total, final_omission, initial_omission, approved, rejected, corrected
            if not isinstance(result, dict):
                return
            key = (
                str((result.get("observation") or {}).get("observationId") or "")
                or str(result.get("recordingId") or "")
                or str(id(result))
            )
            if key in seen_keys:
                return
            seen_keys.add(key)
            total += 1

            analysis = result.get("analysis") or {}
            final_omission += int(bool(analysis.get("possibleFinalConsonantOmission")))
            initial_omission += int(bool(analysis.get("possibleInitialConsonantOmission")))

            for candidate in (result.get("candidates") or [])[:3]:
                if isinstance(candidate, dict):
                    word = candidate.get("word") or candidate.get("candidate")
                    if word:
                        words[str(word)] = words.get(str(word), 0) + 1

            comparison = result.get("phonemeComparison") or {}
            for item in comparison.get("substitutions") or []:
                if isinstance(item, dict):
                    key2 = f"/{item.get('expected','?')}/→/{item.get('observed','?')}/"
                    changed[key2] = changed.get(key2, 0) + 1
            for item in comparison.get("deletions") or []:
                if isinstance(item, dict):
                    key2 = f"/{item.get('expected','?')}/ ({item.get('position','unknown')})"
                    dropped[key2] = dropped.get(key2, 0) + 1

            normalized = review_status.lower()
            approved += int(normalized == "approved_for_learning")
            rejected += int(normalized == "rejected")
            corrected += int(normalized == "corrected_not_approved")

        for wav_path in RECORDINGS_DIR.glob("*.wav"):
            meta = _load_metadata(wav_path)
            consume(meta.get("analysisResult") or {}, str(meta.get("reviewStatus") or ""))

        for result_file in ANALYSIS_RESULTS_DIR.glob("*_analysis.json"):
            try:
                consume(json.loads(result_file.read_text(encoding="utf-8")))
            except Exception:
                pass

        top_words = sorted(words.items(), key=lambda item: item[1], reverse=True)[:15]
        top_changed = sorted(changed.items(), key=lambda item: item[1], reverse=True)[:12]
        top_dropped = sorted(dropped.items(), key=lambda item: item[1], reverse=True)[:12]

        lines = [
            f"Analyzed recordings: {total}",
            f"Possible final-consonant patterns: {final_omission}",
            f"Possible initial-consonant patterns: {initial_omission}",
            f"Approved for learning: {approved}",
            f"Corrected but not approved: {corrected}",
            f"Rejected interpretations: {rejected}",
            "",
            "Most recurring candidate words:",
        ]
        lines.extend([f"  {word}: {count}" for word, count in top_words] or ["  None yet."])
        lines.extend(["", "Most recurring changed sounds:"])
        lines.extend([f"  {pattern}: {count}" for pattern, count in top_changed] or ["  None yet."])
        lines.extend(["", "Most recurring dropped sounds:"])
        lines.extend([f"  {pattern}: {count}" for pattern, count in top_dropped] or ["  None yet."])
        lines.extend([
            "",
            "These counts summarize model outputs and caregiver review history; they are not clinical measurements."
        ])

        self.analytics_box.delete("1.0", "end")
        self.analytics_box.insert("1.0", "\n".join(lines))

    def choose_batch_folder(self):
        if self.batch_running:
            messagebox.showinfo("Batch Analysis", "A batch analysis is already running.")
            return
        folder = filedialog.askdirectory(title="Choose folder containing WAV recordings")
        if not folder:
            return
        files = sorted(Path(folder).glob("*.wav"))
        if not files:
            messagebox.showinfo("Batch Analysis", "No WAV files were found in that folder.")
            return
        if not messagebox.askyesno(
            "Batch Analysis",
            f"Analyze {len(files)} WAV recordings through the Parent PC local API?"
        ):
            return
        self.batch_running = True
        threading.Thread(target=self._batch_worker, args=(files,), daemon=True).start()

    def _batch_worker(self, files: list[Path]):
        ok = 0
        fail = 0
        for index, wav_path in enumerate(files, 1):
            try:
                with wav_path.open("rb") as f:
                    response = requests.post(
                        f"{self.api_base()}/v1/analyze-audio",
                        files={"audio": (wav_path.name, f, "audio/wav")},
                        data={
                            "context": self.context.get().strip(),
                            "speaker_id": self.speaker_id.get().strip() or "anonymous",
                            "session_id": str(uuid.uuid4()),
                            "recording_id": wav_path.stem,
                        },
                        timeout=180
                    )
                response.raise_for_status()
                result = response.json()
                result["_api_url"] = self.api_base()
                _write_analysis_export(wav_path, result)
                ok += 1
            except Exception:
                fail += 1
            self.after(0, lambda i=index: self.status.set(f"Batch analysis {i}/{len(files)}"))

        self.batch_running = False
        self.after(0, self.rebuild_analytics)
        self.after(0, lambda: self.status.set(f"Batch complete • {ok} succeeded • {fail} failed"))

    def open_analysis_results_folder(self):
        ANALYSIS_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        os.startfile(str(ANALYSIS_RESULTS_DIR))

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
                    f"{self.api_base()}/v1/analyze-audio",
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

            result["_api_url"] = self.api_base()
            self.last_analysis_export = _write_analysis_export(wav_path, result)
            result.pop("_api_url", None)

            self.last_result = result
            self.current_file = wav_path
            self.after(0, self._show_result, result)
            self.after(0, self.refresh_history)
            self.after(0, self.refresh_dashboard)
            self.after(0, self.refresh_evidence)
            self.after(0, self.refresh_raw_json)
            self.after(0, self.rebuild_analytics)
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
                    similarity = item.get("phonemeSimilarity")
                    reason = item.get("reason", "")
                    if isinstance(score, (int, float)):
                        suffix = f" • phoneme match {int(similarity * 100)}%" if isinstance(similarity, (int, float)) else ""
                        lines.append(f"{i}. {word}  ({score:.3f}){suffix}")
                    else:
                        lines.append(f"{i}. {word}")
                    if reason:
                        lines.append(f"   Why: {reason}")
                    learned_sub = item.get("learnedSubstitutionEvidence") or {}
                    if isinstance(learned_sub, dict) and learned_sub.get("hasConfirmedPatternSupport"):
                        support = learned_sub.get("weightedSupport", 0)
                        patterns = learned_sub.get("matchedPatterns") or []
                        summary = ", ".join(
                            f"/{p.get('expected','?')}/→/{p.get('observed','?')}/"
                            + (f" {p.get('position')}" if p.get("position") not in (None, "", "unknown") else "")
                            for p in patterns[:3] if isinstance(p, dict)
                        )
                        lines.append(f"   Learned speaker support: {summary} • weight {support}")
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

        prosody = result.get("prosody") or {}
        if isinstance(prosody, dict) and prosody.get("available"):
            lines.append("\nTemporal / prosody:")
            duration = prosody.get("durationSeconds")
            pause_count = prosody.get("pauseCount")
            avg_pause = prosody.get("averagePauseSeconds")
            rate_band = prosody.get("speechRateBand")
            sps = prosody.get("syllablesPerSecond")
            rhythm = prosody.get("rhythmConsistency")
            ending = (prosody.get("endOfUtterance") or {}).get("pattern")
            if isinstance(duration, (int, float)):
                lines.append(f"• Duration: {duration:.2f} seconds")
            if isinstance(pause_count, int):
                if isinstance(avg_pause, (int, float)) and pause_count > 0:
                    lines.append(f"• Pauses: {pause_count} • average {avg_pause:.2f} sec")
                else:
                    lines.append(f"• Pauses: {pause_count}")
            if rate_band:
                if isinstance(sps, (int, float)):
                    lines.append(f"• Speech rate: {rate_band} ({sps:.2f} syllable peaks/sec)")
                else:
                    lines.append(f"• Speech rate: {rate_band}")
            if isinstance(rhythm, (int, float)):
                lines.append(f"• Rhythm consistency: {int(rhythm * 100)}%")
            if ending:
                lines.append(f"• Ending pattern: {str(ending).replace('_', ' ')}")

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
                    f"{self.api_base()}/v1/learning/feedback",
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
            self.refresh_dashboard()
            self.refresh_evidence()
            self.refresh_raw_json()
            self.rebuild_analytics()
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
