"""Caregiver-facing titles and tags for saved recordings.

The index and its append-only audit live in Parent PC user data, never beside
the immutable WAV or the versioned analysis/approval files. Suggested text is
descriptive metadata, NOT recognition evidence or an approval for learning.
"""
from __future__ import annotations

import json
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

_LOCK = threading.RLock()
_WHITESPACE = re.compile(r"\s+")
_MAX_TITLE = 140
_MAX_NOTES = 500
_MAX_TAGS = 12
_MAX_TAG = 40


def _display_text(value: object, limit: int) -> str:
    text = _WHITESPACE.sub(" ", str(value or "")).strip()
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def suggested_title(wav_path: Path, meta: dict, verified_analysis: dict | None = None) -> str:
    """Suggest a title only from explicit saved facts or identified AI guesses.

    No model inference, audio playback, guessed gain setting, or speaker
    attribution is performed during history refresh.
    """
    meta = meta if isinstance(meta, dict) else {}
    notes = _display_text(meta.get("notes"), 90)
    context = _display_text(meta.get("context"), 90)
    background = _display_text(meta.get("backgroundAudioLabel"), 55)
    if background.casefold() == "not specified":
        background = ""
    confirmed = _display_text(meta.get("confirmedWord"), 85)
    status = str(meta.get("reviewStatus") or "").casefold()

    if notes:
        title = "Note: " + notes
    elif context:
        title = "Context: " + context
    elif confirmed and status in {
        "approved", "approved_for_learning", "confirmed", "confirmed_sentence", "confirmed_word"
    }:
        title = "Caregiver confirmed: " + confirmed
    else:
        candidate = ""
        if isinstance(verified_analysis, dict):
            recognition = verified_analysis.get("wordRecognition")
            if isinstance(recognition, dict):
                candidate = _display_text(recognition.get("text"), 85)
        title = "AI suggestion (unverified): " + candidate if candidate else ""

    if background:
        title = (title + " | " if title else "") + background
    if not title:
        source = str(meta.get("source") or "").casefold()
        prefix = "Android recording" if source == "android" else "Parent PC recording"
        stamp = str(meta.get("createdAt") or "")[:16].replace("T", " ")
        title = f"{prefix} — {stamp}" if stamp else f"{prefix} — {wav_path.stem}"
    return _display_text(title, _MAX_TITLE)


def validate_label(title: str, tags: str, notes: str) -> tuple[str, list[str], str]:
    """Reject controls and excessive input; empty title means use suggestion."""
    fields = (str(title).strip(), str(tags).strip(), str(notes).strip())
    if any(any(ord(ch) < 32 and ch not in "\t\n\r" for ch in field) for field in fields):
        raise ValueError("Titles and tags cannot contain control characters.")
    clean_title = _WHITESPACE.sub(" ", fields[0])
    clean_notes = _WHITESPACE.sub(" ", fields[2])
    if len(clean_title) > _MAX_TITLE:
        raise ValueError(f"A recording title can contain at most {_MAX_TITLE} characters.")
    if len(clean_notes) > _MAX_NOTES:
        raise ValueError(f"Recording notes can contain at most {_MAX_NOTES} characters.")
    clean_tags = []
    for raw in fields[1].split(","):
        tag = _WHITESPACE.sub(" ", raw).strip()
        if not tag:
            continue
        if len(tag) > _MAX_TAG:
            raise ValueError(f"Each tag can contain at most {_MAX_TAG} characters.")
        if tag.casefold() not in {item.casefold() for item in clean_tags}:
            clean_tags.append(tag)
    if len(clean_tags) > _MAX_TAGS:
        raise ValueError(f"Use at most {_MAX_TAGS} comma-separated tags.")
    return clean_title, clean_tags, clean_notes


def _identity(wav: Path, meta: dict) -> dict:
    info = wav.stat()
    storage = meta.get("recordingStorage") if isinstance(meta.get("recordingStorage"), dict) else {}
    return {
        "filename": wav.name,
        "recordingId": str(meta.get("recordingId") or ""),
        "audioSha256": str(meta.get("audioSha256") or storage.get("sha256") or ""),
        "bytes": info.st_size,
        "mtimeNs": info.st_mtime_ns,
    }


def _matches_identity(saved: dict, current: dict) -> bool:
    if not isinstance(saved, dict) or saved.get("filename") != current.get("filename"):
        return False
    if saved.get("recordingId") and current.get("recordingId") and saved["recordingId"] != current["recordingId"]:
        return False
    if saved.get("audioSha256") and current.get("audioSha256"):
        return saved["audioSha256"] == current["audioSha256"]
    return saved.get("bytes") == current.get("bytes") and saved.get("mtimeNs") == current.get("mtimeNs")


def _safe_recording(root: Path, wav: Path) -> Path:
    path = wav.resolve()
    if path.parent != root.resolve() or path.suffix.lower() != ".wav" or not path.is_file():
        raise ValueError("Choose an existing recording from the Parent PC recording folder.")
    return path


def load_labels(index_file: Path) -> dict:
    with _LOCK:
        if not index_file.exists():
            return {}
        try:
            data = json.loads(index_file.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as exc:
            raise ValueError("Recording title index cannot be read; labels were not overwritten.") from exc
        if not isinstance(data, dict) or data.get("schemaVersion") != 1 or not isinstance(data.get("recordings"), dict):
            raise ValueError("Recording title index is invalid; labels were not overwritten.")
        if any(not isinstance(key, str) or not isinstance(value, dict) or
               not isinstance(value.get("identity"), dict)
               for key, value in data["recordings"].items()):
            raise ValueError("Recording title index has damaged entries; labels were not overwritten.")
        return data["recordings"]


def label_for_recording(root: Path, wav: Path, meta: dict, stored: dict) -> dict:
    path = _safe_recording(root, wav)
    entry = stored.get(path.name) or {}
    return entry if _matches_identity(entry.get("identity"), _identity(path, meta)) else {}


def _write_index(index_file: Path, values: dict) -> None:
    index_file.parent.mkdir(parents=True, exist_ok=True)
    temp = index_file.with_name(index_file.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temp.open("x", encoding="utf-8") as stream:
            json.dump({"schemaVersion": 1, "recordings": values}, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, index_file)
    finally:
        temp.unlink(missing_ok=True)


def _audit(audit_file: Path, event: dict) -> None:
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    with audit_file.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def save_label(index_file: Path, audit_file: Path, root: Path, wav: Path, meta: dict,
               title: str, tags: str, notes: str) -> dict:
    title, tag_list, notes = validate_label(title, tags, notes)
    with _LOCK:
        path = _safe_recording(root, wav)
        entries = load_labels(index_file)
        previous = label_for_recording(root, path, meta, entries)
        updated = {
            "identity": _identity(path, meta), "customTitle": title,
            "tags": tag_list, "notes": notes,
            "suggestedTitle": str(previous.get("suggestedTitle") or ""),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }
        if any(previous.get(k) != updated.get(k) for k in ("customTitle", "tags", "notes")):
            event = {"eventId": uuid.uuid4().hex, "event": "recording_label_change",
                     "time": updated["updatedAt"], "recording": path.name,
                     "oldLabel": {k: previous.get(k) for k in ("customTitle", "tags", "notes")},
                     "newLabel": {k: updated.get(k) for k in ("customTitle", "tags", "notes")}}
            _audit(audit_file, dict(event, phase="requested"))
            entries[path.name] = updated
            _write_index(index_file, entries)
            _audit(audit_file, dict(event, phase="committed"))
        return updated


def backfill_suggested_labels(index_file: Path, audit_file: Path, root: Path,
                              rows: list[tuple[Path, dict, str]]) -> int:
    """Persist suggestions for older files, preserving every manual field."""
    with _LOCK:
        entries = load_labels(index_file)
        count = 0
        changed = []
        for wav, meta, suggested in rows:
            try:
                path = _safe_recording(root, wav)
                previous = label_for_recording(root, path, meta, entries)
                title = _display_text(suggested, _MAX_TITLE)
                if not title or previous.get("suggestedTitle") == title:
                    continue
                entries[path.name] = {
                    "identity": _identity(path, meta),
                    "customTitle": str(previous.get("customTitle") or ""),
                    "tags": list(previous.get("tags") or []),
                    "notes": str(previous.get("notes") or ""),
                    "suggestedTitle": title,
                    "updatedAt": datetime.now(timezone.utc).isoformat(),
                }
                count += 1
                changed.append({"recording": path.name,
                                "oldSuggestedTitle": str(previous.get("suggestedTitle") or ""),
                                "newSuggestedTitle": title})
            except (OSError, ValueError):
                continue
        if count:
            event = {"eventId": uuid.uuid4().hex, "event": "suggested_titles_saved",
                     "time": datetime.now(timezone.utc).isoformat(), "count": count,
                     "changes": changed}
            _audit(audit_file, dict(event, phase="requested"))
            _write_index(index_file, entries)
            _audit(audit_file, dict(event, phase="committed"))
        return count
