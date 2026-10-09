"""Persistent learning store for First Sound Helper / Hearlium.

Phase 1 goals:
- Keep observations append-only and hash-verified.
- Keep interpretations separate from observations.
- Accept human feedback linked by observation_id.
- Only approved examples update the speaker profile.
- Track simple outcome/evaluation metrics from confirmed feedback.
- Do not auto-retrain a model.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

_LOCK = threading.RLock()

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _canonical(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def _hash(obj: Dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(obj).encode("utf-8")).hexdigest()

def _safe_id(value: str) -> str:
    value = (value or "").strip()
    return "".join(ch for ch in value if ch.isalnum() or ch in "-_")[:128] or "anonymous"

class LearningStore:
    def __init__(self, root: Optional[str] = None):
        base = root or os.getenv("FSH_DATA_DIR", "./data")
        self.root = Path(base)
        self.root.mkdir(parents=True, exist_ok=True)
        self.observations = self.root / "observations.jsonl"
        self.interpretations = self.root / "interpretations.jsonl"
        self.feedback = self.root / "feedback.jsonl"
        self.approved = self.root / "approved_learning_examples.jsonl"
        self.profiles = self.root / "speaker_profiles"
        self.profiles.mkdir(parents=True, exist_ok=True)

    def _append(self, path: Path, obj: Dict[str, Any]) -> None:
        with _LOCK:
            with path.open("a", encoding="utf-8") as f:
                f.write(_canonical(obj) + "\n")

    def _iter(self, path: Path):
        if not path.exists():
            return
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    continue

    def save_observation(self, observation: Dict[str, Any], speaker_id: str = "") -> Dict[str, Any]:
        snapshot = deepcopy(observation)
        record = {
            "recordType": "immutable_observation",
            "speakerId": _safe_id(speaker_id),
            "storedAt": _now(),
            "observation": snapshot,
            "observationHash": _hash(snapshot),
        }
        self._append(self.observations, record)
        return deepcopy(record)

    def save_interpretation(
        self,
        observation_id: str,
        recording_id: str,
        speaker_id: str,
        candidates: list,
        best_candidate: Optional[Dict[str, Any]],
        confidence: float,
        uncertainty: str,
        context: str,
    ) -> Dict[str, Any]:
        record = {
            "recordType": "interpretation",
            "storedAt": _now(),
            "speakerId": _safe_id(speaker_id),
            "observationId": observation_id,
            "recordingId": recording_id,
            "candidates": deepcopy(candidates),
            "bestCandidate": deepcopy(best_candidate or {}),
            "confidence": confidence,
            "uncertaintyBand": uncertainty,
            "context": context or "",
        }
        self._append(self.interpretations, record)
        return deepcopy(record)

    def find_observation(self, observation_id: str) -> Optional[Dict[str, Any]]:
        found = None
        for rec in self._iter(self.observations) or []:
            obs = rec.get("observation", {})
            if obs.get("observationId") == observation_id:
                found = rec
        if not found:
            return None
        # Verify immutable snapshot has not changed on disk.
        obs = found.get("observation", {})
        found["hashValid"] = (_hash(obs) == found.get("observationHash"))
        return deepcopy(found)

    def latest_interpretation(self, observation_id: str) -> Optional[Dict[str, Any]]:
        found = None
        for rec in self._iter(self.interpretations) or []:
            if rec.get("observationId") == observation_id:
                found = rec
        return deepcopy(found) if found else None

    def _profile_path(self, speaker_id: str) -> Path:
        return self.profiles / f"{_safe_id(speaker_id)}.json"

    def get_profile(self, speaker_id: str) -> Dict[str, Any]:
        sid = _safe_id(speaker_id)
        p = self._profile_path(sid)
        if not p.exists():
            return {
                "speakerId": sid,
                "approvedExamples": 0,
                "wordHistory": {},
                "patternHistory": {},
                "heardToMeaning": {},
                "learningHistory": {
                    "examples": 0, "patterns": {}, "words": {},
                    "strategies": {}, "evaluated": 0, "correct": 0
                },
            }
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _write_profile(self, speaker_id: str, profile: Dict[str, Any]) -> None:
        p = self._profile_path(speaker_id)
        tmp = p.with_suffix(".tmp")
        with _LOCK:
            tmp.write_text(_canonical(profile), encoding="utf-8")
            tmp.replace(p)

    def submit_feedback(
        self,
        speaker_id: str,
        observation_id: str,
        recording_id: str = "",
        confirmed_word: str = "",
        corrected_word: str = "",
        approved_for_learning: bool = False,
        source: str = "caregiver",
    ) -> Dict[str, Any]:
        sid = _safe_id(speaker_id)
        obs_rec = self.find_observation(observation_id)
        if not obs_rec:
            raise ValueError("observation_not_found")
        if not obs_rec.get("hashValid", False):
            raise ValueError("observation_hash_mismatch")

        obs = deepcopy(obs_rec["observation"])
        interpretation = self.latest_interpretation(observation_id) or {}
        chosen = (corrected_word or confirmed_word or "").strip().lower()
        best_word = str((interpretation.get("bestCandidate") or {}).get("word", "")).strip().lower()

        feedback_record = {
            "recordType": "human_feedback",
            "feedbackId": hashlib.sha256(f"{observation_id}|{_now()}".encode()).hexdigest()[:24],
            "storedAt": _now(),
            "speakerId": sid,
            "observationId": observation_id,
            "recordingId": recording_id or obs.get("recordingId", ""),
            "confirmedWord": (confirmed_word or "").strip().lower(),
            "correctedWord": (corrected_word or "").strip().lower(),
            "approvedForLearning": bool(approved_for_learning),
            "source": source,
            "observationHash": obs_rec["observationHash"],
        }
        self._append(self.feedback, feedback_record)

        profile_updated = False
        if approved_for_learning and chosen:
            candidate = interpretation.get("bestCandidate") or {}
            pattern = str(candidate.get("pattern", "")).strip()
            heard = str(obs.get("transcript", "")).strip().lower()

            approved_record = {
                "recordType": "approved_learning_example",
                "approvedAt": _now(),
                "speakerId": sid,
                "observationId": observation_id,
                "recordingId": feedback_record["recordingId"],
                "observationHash": obs_rec["observationHash"],
                "heard": heard,
                "targetWord": chosen,
                "pattern": pattern,
                "context": interpretation.get("context", ""),
                "modelWasCorrect": bool(best_word and best_word == chosen),
            }
            self._append(self.approved, approved_record)

            profile = self.get_profile(sid)
            profile["speakerId"] = sid
            profile["approvedExamples"] = int(profile.get("approvedExamples", 0)) + 1

            wh = profile.setdefault("wordHistory", {})
            wh[chosen] = int(wh.get(chosen, 0)) + 1

            ph = profile.setdefault("patternHistory", {})
            if pattern:
                ph[pattern] = int(ph.get(pattern, 0)) + 1

            htm = profile.setdefault("heardToMeaning", {})
            if heard:
                per_heard = htm.setdefault(heard, {})
                per_heard[chosen] = int(per_heard.get(chosen, 0)) + 1

            lh = profile.setdefault("learningHistory", {})
            lh["examples"] = int(lh.get("examples", 0)) + 1
            words = lh.setdefault("words", {})
            words[chosen] = int(words.get(chosen, 0)) + 1
            patterns = lh.setdefault("patterns", {})
            if pattern:
                patterns[pattern] = int(patterns.get(pattern, 0)) + 1
            lh["evaluated"] = int(lh.get("evaluated", 0)) + 1
            if best_word and best_word == chosen:
                lh["correct"] = int(lh.get("correct", 0)) + 1

            profile["lastUpdated"] = _now()
            self._write_profile(sid, profile)
            profile_updated = True

        return {
            "accepted": True,
            "approvedForLearning": bool(approved_for_learning),
            "profileUpdated": profile_updated,
            "speakerId": sid,
            "observationId": observation_id,
        }

    def integrity_status(self) -> Dict[str, Any]:
        total = 0
        valid = 0
        for rec in self._iter(self.observations) or []:
            total += 1
            obs = rec.get("observation", {})
            if _hash(obs) == rec.get("observationHash"):
                valid += 1
        return {"observations": total, "hashValid": valid, "hashInvalid": total - valid}
