"""Crash-resistant, non-destructive persistence for caregiver word reviews.

Every approved clip is stored under a unique transaction directory; existing clips
are never overwritten. Write and validate every clip before atomically publishing
its review manifest. An interrupted save may leave an unreferenced directory, but
must never make an incomplete clip appear in a committed review manifest.
"""
from __future__ import annotations

import copy
import json
import os
import shutil
import threading
import uuid
from pathlib import Path
from typing import Any, Callable


# Commit operations on one recording are serialized to avoid lost review history.
_REVIEW_LOCKS_GUARD = threading.Lock()
_REVIEW_LOCKS: dict[str, threading.RLock] = {}


def _review_lock(path: Path) -> threading.RLock:
    with _REVIEW_LOCKS_GUARD:
        return _REVIEW_LOCKS.setdefault(str(path.resolve()), threading.RLock())


def reusable_previous_reviews(
    saved: dict[str, Any], observation_id: str | None,
    segments: list[dict[str, Any]], *, tolerance: float = .001,
) -> dict[str, dict[str, Any]]:
    """Reuse approvals only when their observation and exact clip align.

    Legacy manifests without an observation ID are never auto-confirmed.
    Even within one observation, changed boundaries or words must be reviewed
    afresh. This does not delete old decisions from the archived audit history.
    """
    if not isinstance(saved, dict) or not isinstance(saved.get("reviews"), dict):
        return {}
    current_id = str(observation_id or "").strip()
    if not current_id or current_id != str(saved.get("observationId") or "").strip():
        return {}
    previous = saved["reviews"]
    valid = {}
    for segment in segments:
        try:
            idx = str(int(segment.get("segmentIndex")))
            old = previous.get(idx)
            if not isinstance(old, dict):
                continue
            start = float(segment["startSeconds"])
            end = float(segment["endSeconds"])
            old_start = float(old["startSeconds"])
            old_end = float(old["endSeconds"])
            if not (abs(start - old_start) <= tolerance and abs(end - old_end) <= tolerance):
                continue
            if str(segment.get("suggestedWord") or "").strip().casefold() != str(old.get("suggestedWord") or "").strip().casefold():
                continue
            if str(segment.get("observedPhonemes") or "").strip() != str(old.get("observedPhonemes") or "").strip():
                continue
            valid[idx] = old
        except (ValueError, KeyError, TypeError):
            continue
    return valid


def commit_review_manifest(
    wav_path: Path,
    review_path: Path,
    reviews: dict[str, Any],
    approved_clips_dir: Path,
    *,
    audio_reader: Callable | None = None,
    clip_writer: Callable | None = None,
) -> dict[str, Any]:
    """Serialize commits on this recording and preserve the previous manifest."""
    with _review_lock(review_path):
        return _commit_review_manifest_locked(
            wav_path, review_path, reviews, approved_clips_dir,
            audio_reader=audio_reader, clip_writer=clip_writer,
        )


def _commit_review_manifest_locked(
    wav_path: Path,
    review_path: Path,
    reviews: dict[str, Any],
    approved_clips_dir: Path,
    *,
    audio_reader: Callable | None = None,
    clip_writer: Callable | None = None,
) -> dict[str, Any]:
    """Commit a complete, versioned review manifest or leave the previous one intact.

    The caller supplies already-validated decisions. Clip writers/readers can be
    injected by tests to simulate disk or codec failures. Earlier approved clips
    are intentionally retained for audit/rollback rather than garbage-collected.
    """
    if not wav_path.is_file():
        raise FileNotFoundError(f"Original recording not found: {wav_path}")
    if not isinstance(reviews, dict) or not isinstance(reviews.get("reviews"), dict):
        raise ValueError("A complete review manifest is required")

    # Only local copies are amended; failed commits cannot mutate UI state.
    payload = copy.deepcopy(reviews)
    rows = payload["reviews"]
    eligible = [r for r in rows.values() if r.get("status") == "confirmed"]
    approved_clips_dir.mkdir(parents=True, exist_ok=True)
    review_path.parent.mkdir(parents=True, exist_ok=True)

    transaction_id = uuid.uuid4().hex
    previous_manifest = review_path.read_bytes() if review_path.is_file() else None
    # Full prior decision records, labels, observation links and clip references
    # are archived before latest.json is replaced. Archives are never overwritten.
    history_dir = review_path.parent / "history" / review_path.stem
    archive_file = history_dir / f"previous_{transaction_id}.json"
    archive_tmp = history_dir / f".pending_previous_{transaction_id}"
    archive_created = False
    payload["revisionId"] = transaction_id
    if previous_manifest is not None:
        try:
            previous = json.loads(previous_manifest)
        except (ValueError, TypeError):
            previous = {}
        payload["previousRevisionId"] = previous.get("revisionId") if isinstance(previous, dict) else None
    # Stable basename is descriptive, but a new UUID prevents overwriting a
    # previously approved clip, even if a previous review uses the same indices.
    final_dir = approved_clips_dir / f"{wav_path.stem}_{transaction_id}"
    stage_dir = approved_clips_dir / f".pending_{transaction_id}"
    manifest_tmp = review_path.with_name(f"{review_path.name}.pending_{transaction_id}")
    published_clips = False
    manifest_committed = False
    try:
        if eligible:
            if audio_reader is None or clip_writer is None:
                import soundfile as sf
                audio_reader = audio_reader or sf.read
                clip_writer = clip_writer or sf.write
            audio, rate = audio_reader(str(wav_path), dtype="float32", always_2d=False)
            if rate <= 0:
                raise ValueError("The recording's sample rate is invalid")
            stage_dir.mkdir(parents=True, exist_ok=False)
            for row in eligible:
                start = float(row["startSeconds"])
                end = float(row["endSeconds"])
                if not (0 <= start < end):
                    raise ValueError("An approved word has invalid time boundaries")
                lo = max(0, int(start * rate))
                hi = min(len(audio), int(end * rate))
                if hi <= lo:
                    raise ValueError("An approved word contains no playable audio")
                index = int(row["segmentIndex"])
                name = f"segment_{index:03d}.wav"
                if (stage_dir / name).exists():
                    raise ValueError("Duplicate word segment index")
                clip_writer(str(stage_dir / name), audio[lo:hi], rate, subtype="PCM_16")
                # A successful writer should have produced a nonempty file.
                if not (stage_dir / name).is_file() or (stage_dir / name).stat().st_size == 0:
                    raise OSError(f"Word clip was not written: {name}")
                row["approvedClip"] = str(final_dir / name)
                row["approvedForLearning"] = True
        for row in rows.values():
            if row.get("status") != "confirmed":
                row.pop("approvedClip", None)
                row["approvedForLearning"] = False

        manifest_tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        if previous_manifest is not None:
            history_dir.mkdir(parents=True, exist_ok=True)
            # If an archival write fails, abort BEFORE publishing the new manifest.
            with archive_tmp.open("xb") as prior_out:
                prior_out.write(previous_manifest)
                prior_out.flush()
                os.fsync(prior_out.fileno())
            os.replace(archive_tmp, archive_file)
            archive_created = True
        # Make all new clips visible before replacing the one authoritative manifest.
        if eligible:
            os.replace(stage_dir, final_dir)
            published_clips = True
        os.replace(manifest_tmp, review_path)
        manifest_committed = True
        return payload
    finally:
        if not manifest_committed:
            manifest_tmp.unlink(missing_ok=True)
            if stage_dir.exists():
                shutil.rmtree(stage_dir)
            # Only remove the newly created transaction, never an old clip.
            if published_clips and final_dir.exists():
                shutil.rmtree(final_dir)
            archive_tmp.unlink(missing_ok=True)
            if archive_created:
                archive_file.unlink(missing_ok=True)
