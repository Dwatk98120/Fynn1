from __future__ import annotations

import json
import os
import queue
import threading
import time
import uuid
import wave
import re
from datetime import datetime
from pathlib import Path

import requests
from analysis_client import analyze_saved_wav
from analysis_consistency import (
    ObservationChanged, SavedAnalysisMismatch, load_verified_saved_analysis, observation_id,
)
from caregiver_approval_integrity import (
    ReviewDecisionSuperseded, require_verified_loaded_analysis, review_revision,
)
from api_diagnostics import write_event
from review_evidence_store import commit_review_manifest, reusable_previous_reviews
from student_recording_library import (
    load_profiles, assign_display_name, student_display_name,
    is_unassigned, filter_and_sort, parse_day,
)
from recording_title_store import (
    suggested_title, load_labels, label_for_recording,
    save_label, backfill_suggested_labels,
)
from caregiver_review_guidance import (
    DECISION_TO_STATUS, display_decision, confirmation_issue, caregiver_explanation,
)
import sounddevice as sd
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from reanalysis_integrity import snapshot as integrity_snapshot, save_report as save_integrity_report
from capture_identity import capture_identity

# Runtime data must never be created under Program Files or the PyInstaller bundle.
ROOT = Path(__file__).resolve().parents[1]
USER_DATA = Path(os.getenv("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "Hearlium" / "ParentPC"
RECORDINGS_DIR = Path(os.getenv("FSH_RECORDINGS_DIR") or (USER_DATA / "recordings"))
ANALYSIS_RESULTS_DIR = USER_DATA / "analysis_results"
SEGMENT_REVIEWS_DIR = USER_DATA / "segment_reviews"
APPROVED_CLIPS_DIR = SEGMENT_REVIEWS_DIR / "approved_clips"
CONFIG_PATH = USER_DATA / "parent_pc_config.json"
STUDENT_PROFILES_PATH = USER_DATA / "student_profiles.json"
STUDENT_PROFILE_AUDIT_PATH = USER_DATA / "student_profile_audit.jsonl"
RECORDING_TITLES_PATH = USER_DATA / "recording_titles.json"
RECORDING_TITLES_AUDIT_PATH = USER_DATA / "recording_titles_audit.jsonl"
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
SEGMENT_REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
APPROVED_CLIPS_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"
DEFAULT_API_URL = "http://127.0.0.1:8000"
PARENT_PC_SOURCE_REVIEW_VERSION = "layer2-background-vocal-review-v1"
BACKGROUND_AUDIO_REVIEW_VERSION = "layer2-background-vocals-human-review-v1"
BACKGROUND_AUDIO_LABELS = (
    "Not specified", "Ambient noise (no known voices)",
    "Music without singing", "Music with singing",
    "Distant conversation", "Mixed sounds / unsure",
)


def _background_audio_label(value):
    return value if isinstance(value, str) and value in BACKGROUND_AUDIO_LABELS else "Not specified"


def _phoneme_review_warning_lines(result: dict) -> list[str]:
    """Explain an unverified timing mismatch without rewriting CTC evidence."""
    timing = result.get("phonemeTimingReview") or {}
    if not isinstance(timing, dict):
        return []
    late = timing.get("uncorroboratedLateSegmentCount") or 0
    held = timing.get("automaticWordSuggestionHoldCount") or 0
    extended = timing.get("extendedWordSegmentNeedsReview") is True
    if not (isinstance(late, int) and late > 0) and not extended:
        return []

    def seconds(value):
        return f"{value:.2f}s" if isinstance(value, (int, float)) else "unverified"

    lines = [
        "",
        "PHONEME TIMING WARNING — HUMAN REVIEW NEEDED",
        f"Unverified word-recognizer end: {seconds(timing.get('wordAsrEndSeconds'))}; "
        f"phoneme output end: {seconds(timing.get('phonemeCandidateEndSeconds'))}.",
        f"{late} late phoneme segment(s) flagged; {held} automatic word suggestion(s) withheld.",
        "These may contain background noise, distant voices, or genuine speech.",
        "A song with singing can produce real vocal/phoneme activity from a NON-TARGET voice.",
        "No speaker identity or true speech endpoint is established by these timings.",
        "Raw phonemes remain preserved. Never approve learning without listening and review.",
    ]
    if extended:
        lines.append("The word recognizer's segment may be stretched; its end time is uncertain.")
    return lines


def _recognition_diagnostic_lines(result):
    review = result.get('recognitionDiagnostics') or {}
    if not review:
        return []
    lines = ["", "WORD TIMING / REPETITION REVIEW",
             f"Transcript tokens: {review.get('transcriptTokenCount')}; timed tokens: {review.get('timedTokenCount')}; unresolved phoneme segments: {review.get('unresolvedPhonemeAlignmentCount')}."]
    if not review.get('timingTokenCountsMatch'):
        lines.append("Some transcript words have missing or mismatched timing; no boundaries were invented.")
    if review.get('broadTimedWordIndices') or review.get('veryShortTimedWordIndices'):
        lines.append("Unusually broad or short word intervals need listening review.")
    if review.get('boundaryRepetitions') or review.get('adjacentRepeatedCandidates'):
        lines.append("Possible repeated words or differing repetition evidence: listen before accepting. Genuine repetitions are preserved.")
    lines.append("Candidate omission flags are unverified. Insufficient evidence means pronunciation omissions cannot be assessed.")
    alternatives = result.get('phonemeBoundaryAlternatives') or []
    alignment = result.get('wordPhonemeAlignmentReview') or {}
    groups = alignment.get('groupedAlignmentCandidates') or []
    lines.append(f"Boundary review: {len(alternatives)} alternative split/join proposals; {len(groups)} timing-overlap groups. None are confirmed words.")
    if (result.get('recordingStorage') or {}).get('legacyAliasCorroboration'):
        lines.append('Legacy copy corroborated against a separate verified receipt. Its missing provenance remains unknown; original files were preserved.')
    return lines


def _raw_phoneme_preview(value, *, limit=180) -> str:
    """Shorten screen text only; original observations and JSON stay complete."""
    raw = str(value or "").strip()
    if not raw:
        return "Unavailable"
    if len(raw) <= limit:
        return raw
    return f"{raw[:limit].rstrip()}… [first {limit} of {len(raw)} characters; full raw output in Evidence / Raw JSON]"



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


def _write_analysis_export(wav_path: Path, result: dict, *, destination: Path | None = None) -> Path:
    """Publish a complete JSON export atomically; never expose half-written JSON."""
    out = destination if destination is not None else _safe_analysis_filename(wav_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(result)
    payload["_parent_pc"] = {
        "file": str(wav_path),
        "api_url": payload.get("_api_url", ""),
        "saved_at": datetime.now().isoformat(timespec="seconds"),
    }
    payload.pop("_api_url", None)
    stage = out.with_name(f"{out.name}.{uuid.uuid4().hex}.tmp")
    try:
        stage.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(stage, out)
    finally:
        stage.unlink(missing_ok=True)
    return out


def _append_feedback_observation_audit(wav_path: Path, expected: str, actual: str, response: dict) -> Path:
    """Preserve an API-accepted reply for the *old* observation, never approve the new one.

    Kept separately from API health telemetry, which intentionally excludes
    identifiable student and caregiver review data.
    """
    audit_dir = USER_DATA / "feedback_observation_audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_path = audit_dir / f"{wav_path.stem}_{uuid.uuid4().hex}.json"
    entry = {"recordingFile": str(wav_path), "expectedObservationId": expected,
             "currentObservationId": actual, "receivedAt": datetime.now().isoformat(timespec="seconds"),
             "apiFeedbackResponse": response,
             "reason": "API accepted feedback for a superseded observation; current review not changed"}
    stage = audit_path.with_name(audit_path.name + ".tmp")
    try:
        stage.write_text(json.dumps(entry, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        os.replace(stage, audit_path)
    finally:
        stage.unlink(missing_ok=True)
    return audit_path



def _write_feedback_audit_update(audit_path: Path, changes: dict) -> None:
    """Update the recovery record after attempting to revoke a stale approval."""
    entry = json.loads(audit_path.read_text(encoding="utf-8"))
    entry.update(changes)
    stage = audit_path.with_name(f"{audit_path.name}.{uuid.uuid4().hex}.tmp")
    try:
        stage.write_text(json.dumps(entry, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        os.replace(stage, audit_path)
    finally:
        stage.unlink(missing_ok=True)


def _revoke_remote_approval(api_url: str, speaker_id: str, feedback_response: dict, *, reason: str) -> dict:
    """Revoke an accepted but superseded approval via the local-only ledger API."""
    if not feedback_response.get("approvedForLearning"):
        return {"status": "not_approved"}
    example_id = str(feedback_response.get("exampleId") or "").strip()
    if not example_id:
        raise RuntimeError("The server accepted approval but omitted the example ID; inspect Learning History for manual rollback.")
    from urllib.parse import urlsplit
    parsed = urlsplit(api_url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Invalid Parent PC API address for revocation")
    # This route is local-PC-only. Do not send administrative rollback to Android
    # or other remote hosts, even if the original feedback URL was a LAN address.
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    revoke_url = f"http://127.0.0.1:{port}/v1/learning/revoke"
    response = requests.post(revoke_url, data={
        "speaker_id": speaker_id, "example_id": example_id, "reason": reason,
    }, timeout=20)
    response.raise_for_status()
    result = response.json()
    if not isinstance(result, dict) or not result.get("revoked") or str(result.get("exampleId")) != example_id:
        raise RuntimeError("Learning server did not confirm revocation of the superseded approval")
    return {"status": "revoked", "exampleId": example_id, "serverResponse": result}


def _audit_and_revoke_superseded_approval(
    wav_path: Path, expected_observation: str, current_observation: str,
    feedback_response: dict, *, api_url: str, speaker_id: str,
    expected_revision: int, current_revision: int,
) -> dict:
    """Durably audit the response BEFORE attempting remote rollback.

    If the server is unreachable, keep a visible recovery file rather than
    pretending a caregiver's rejection successfully revoked remote learning.
    """
    audit = _append_feedback_observation_audit(
        wav_path, expected_observation, current_observation, feedback_response)
    _write_feedback_audit_update(audit, {
        "reason": "Superseded by a newer caregiver decision or observation",
        "expectedReviewRevision": expected_revision,
        "currentReviewRevision": current_revision,
        "revocationStatus": "pending" if feedback_response.get("approvedForLearning") else "not_needed",
    })
    if not feedback_response.get("approvedForLearning"):
        return {"revoked": True, "auditPath": str(audit), "notNeeded": True}
    try:
        outcome = _revoke_remote_approval(
            api_url, speaker_id, feedback_response, reason="superseded_caregiver_decision")
    except Exception as exc:
        _write_feedback_audit_update(audit, {
            "revocationStatus": "ACTION_REQUIRED", "revocationError": str(exc),
        })
        return {"revoked": False, "auditPath": str(audit), "error": str(exc)}
    _write_feedback_audit_update(audit, {"revocationStatus": "revoked", "revocationResult": outcome})
    return {"revoked": True, "auditPath": str(audit)}


def _approval_refs(meta: dict) -> list[dict]:
    """Versioned local pointers to server examples; never drop an accepted approval.

    Legacy builds kept only learningFeedback.  Import that accepted approval
    once so a subsequent correction cannot erase its remote example ID.
    """
    refs = [dict(row) for row in (meta.get("learningApprovalReferences") or [])
            if isinstance(row, dict) and str(row.get("exampleId") or "").strip()]
    response = meta.get("learningFeedback")
    if isinstance(response, dict) and response.get("approvedForLearning"):
        example_id = str(response.get("exampleId") or "").strip()
        if example_id and not any(str(row.get("exampleId")) == example_id for row in refs):
            refs.append({"exampleId": example_id,
                         "speakerId": str(meta.get("speakerId") or response.get("speakerId") or ""),
                         "observationId": str(response.get("observationId") or meta.get("observationId") or ""),
                         "recordingId": str(meta.get("recordingId") or ""),
                         "status": "active", "source": "legacy_learningFeedback"})
    return refs


def _active_approval(meta: dict) -> dict | None:
    refs = _approval_refs(meta)
    for row in reversed(refs):
        if row.get("status", "active") != "revoked":
            return row
    response = meta.get("learningFeedback")
    if isinstance(response, dict) and response.get("approvedForLearning") and not response.get("exampleId"):
        # If the API omitted its ID there is nothing safe to revoke automatically.
        return {"exampleId": "", "speakerId": str(meta.get("speakerId") or ""),
                "observationId": str(meta.get("observationId") or ""),
                "recordingId": str(meta.get("recordingId") or ""), "status": "active"}
    return None


def _mark_approval_revoked(meta: dict, example_id: str) -> list[dict]:
    refs = _approval_refs(meta)
    for ref in refs:
        if (str(ref.get("exampleId") or "") == example_id and
                ref.get("status", "active") != "revoked"):
            ref["status"] = "revoked"
            ref["revokedAt"] = datetime.now().isoformat(timespec="seconds")
    return refs


def _remember_new_approval(meta: dict, response: dict, speaker: str, observation: str,
                           request_id: str = "") -> list[dict]:
    refs = _approval_refs(meta)
    if response.get("approvedForLearning"):
        example_id = str(response.get("exampleId") or "").strip()
        if not example_id:
            raise ValueError("Learning API accepted approval without example ID; manual reconciliation required")
        if not any(str(row.get("exampleId") or "") == example_id for row in refs):
            refs.append({"exampleId": example_id, "speakerId": speaker,
                         "observationId": observation,
                         "recordingId": str(meta.get("recordingId") or ""),
                         "requestId": str(response.get("clientRequestId") or request_id or ""),
                         "status": "active", "source": "approved_caregiver_feedback"})
    return refs


def _resolve_definite_feedback_rejection(wav_path: Path, request_id: str, observation: str) -> dict:
    """A definite 4xx means this request was rejected, even after Unsure/Reject.

    Identify the original request, not the current review revision. Never
    clear an unrelated pending approval or rollback failure.
    """
    def update(meta):
        changed = {}
        for key in ("feedbackPending", "supersededFeedbackPending"):
            if _matching_feedback_request(meta.get(key), request_id, observation):
                changed[key] = None
        if changed and str(meta.get("learningRevocationRequestId") or "") == request_id:
            if meta.get("learningRevocationStatus") in ("awaiting_api_resolution", "ACTION_REQUIRED"):
                changed["learningRevocationStatus"] = None
            changed["learningRevocationRequestId"] = None
        return changed
    return _update_metadata(wav_path, update)


def _reconcile_manual_learning_revocation(example: dict, speaker_id: str) -> dict:
    """Reconcile a server-confirmed manual revoke with matching WAV metadata.

    Clear a pending request only when an exact request ID links it to the
    revoked server example, not just a matching recording/observation.
    Legacy data that cannot be matched is diagnosed, NEVER guessed or cleared.
    Called only AFTER /v1/learning/revoke explicitly confirms the example ID.
    """
    example_id = str(example.get("exampleId") or "").strip()
    target_recording = str(example.get("recordingId") or "").strip()
    target_observation = str(example.get("observationId") or "").strip()
    server_request_id = str(example.get("clientRequestId") or "").strip()
    speaker_id = str(speaker_id or "").strip()
    if not (example_id and target_recording and target_observation and speaker_id):
        return {"updated": 0, "note": "Server example has incomplete identity; local warnings left intact"}
    count = 0
    metadata_scanned = 0
    recording_matches = 0
    linked_examples = 0
    for wav in RECORDINGS_DIR.rglob("*.wav"):
        if not wav.is_file() or not _metadata_path(wav).exists():
            continue
        def update(meta):
            if (str(meta.get("speakerId") or "") != speaker_id or
                str(meta.get("recordingId") or "") != target_recording):
                return {}
            refs = _approval_refs(meta)
            matched_refs = [ref for ref in refs if
                str(ref.get("exampleId") or "") == example_id and
                str(ref.get("observationId") or target_observation) == target_observation]
            direct_match = bool(matched_refs)
            legacy = meta.get("learningFeedback") or {}
            direct_match = direct_match or (isinstance(legacy, dict) and
                str(legacy.get("exampleId") or "") == example_id and
                str(legacy.get("observationId") or target_observation) == target_observation)
            expected_id_match = str(meta.get("learningRevocationExampleId") or "") == example_id
            missing_id_record = meta.get("learningUnresolvedApprovedFeedback") or {}
            possible_legacy_match = (isinstance(missing_id_record, dict) and
                missing_id_record.get("approvedForLearning") and
                not missing_id_record.get("exampleId") and
                str(missing_id_record.get("observationId") or "") == target_observation and
                example.get("segmentIndex") is None)
            local_request_ids = {str(ref.get("requestId") or "").strip()
                                 for ref in matched_refs if ref.get("requestId")}
            identity_conflict = bool(server_request_id and local_request_ids and
                                     local_request_ids != {server_request_id})
            request_ids = set() if identity_conflict else (
                {server_request_id} if server_request_id else local_request_ids)
            request_ids.discard("")
            def exact_request(mark):
                return (isinstance(mark, dict) and
                        mark.get("reviewStatus") == "approved_for_learning" and
                        str(mark.get("observationId") or "") == target_observation and
                        str(mark.get("requestId") or "") in request_ids and
                        bool(mark.get("requestId")))
            marker_match = any(exact_request(meta.get(k)) for k in
                               ("feedbackPending", "supersededFeedbackPending"))
            unresolved_legacy_match = possible_legacy_match and marker_match
            if not (direct_match or expected_id_match or marker_match or unresolved_legacy_match):
                return {}
            changed = {}
            if direct_match or expected_id_match or unresolved_legacy_match:
                changed["learningApprovalReferences"] = _mark_approval_revoked(meta, example_id)
            if unresolved_legacy_match:
                changed["learningUnresolvedApprovedFeedback"] = None
                changed["learningApprovalReferences"].append({
                    "exampleId": example_id, "speakerId": speaker_id,
                    "recordingId": target_recording, "observationId": target_observation,
                    "requestId": server_request_id,
                    "status": "revoked", "source": "manual_legacy_reconciliation"})
            if expected_id_match or direct_match or unresolved_legacy_match:
                changed["learningRevocationExampleId"] = None
                changed["learningRevocationId"] = None
            # Repeated requests may share the observation ID.
            for key in ("feedbackPending", "supersededFeedbackPending"):
                mark = meta.get(key)
                if exact_request(mark):
                    changed[key] = None
            has_other_markers = any(meta.get(k) and k not in changed for k in
                                    ("feedbackPending", "supersededFeedbackPending"))
            failure_request = str(meta.get("learningRevocationRequestId") or "")
            other_example = str(meta.get("learningRevocationExampleId") or "")
            if (not has_other_markers and not identity_conflict and
                (not failure_request or failure_request in request_ids) and
                (not other_example or other_example == example_id) and
                (direct_match or expected_id_match or marker_match or unresolved_legacy_match)):
                changed["learningRevocationStatus"] = "revoked"
                changed["learningRevocationRequestId"] = None
            return changed
        with _metadata_lock(wav):
            before = _load_metadata(wav)
            metadata_scanned += 1
            if (str(before.get("speakerId") or "") == speaker_id and
                str(before.get("recordingId") or "") == target_recording):
                recording_matches += 1
                refs = _approval_refs(before)
                if any(str(ref.get("exampleId") or "") == example_id for ref in refs):
                    linked_examples += 1
            delta = update(before)
            effective = {key: value for key, value in delta.items() if before.get(key) != value}
            if effective:
                _update_metadata(wav, effective)
                count += 1
    if count:
        note = f"Safely reconciled {count} matching local recording(s)."
    elif not metadata_scanned:
        note = ("No local WAV metadata was found under the current recordings folder. "
                "Older or archived recordings may be elsewhere; no warnings were cleared.")
    elif not recording_matches:
        note = ("No local recording matched the server's exact speaker and recording IDs. "
                "Check legacy storage locations; no warnings were cleared.")
    elif not linked_examples:
        note = ("A recording ID matched, but its metadata did not identify this approved "
                "example. Do not link by word or observation alone; warnings remain unchanged.")
    else:
        note = ("Matching approval references were found, but no metadata change was "
                "needed or safely justified. Verify any warning against its request ID.")
    return {"updated": count, "exampleId": example_id,
            "recordingMatches": recording_matches, "linkedExamples": linked_examples,
            "note": note}


def _has_unresolved_learning_feedback(meta: dict) -> bool:
    """A rollback/unknown approval stays a gate across review revisions.

    Never treat `pending` as a completed rollback.  The UI may advance its
    decision revision while the network worker is running, but that does not
    revoke an earlier example on the learning server.
    """
    return bool(
        meta.get("feedbackPending") or meta.get("supersededFeedbackPending") or
        meta.get("learningRevocationStatus") in
        ("pending", "awaiting_api_resolution", "ACTION_REQUIRED")
    )


def _matching_feedback_request(marker, request_id: str, observation: str) -> bool:
    """Only resolve the exact in-flight request, not a subsequent operation."""
    if not isinstance(marker, dict):
        return False
    marker_id = str(marker.get("requestId") or "")
    if marker_id or request_id:
        return bool(marker_id and marker_id == request_id)
    # Backwards compatibility with metadata created before request IDs existed.
    return (str(marker.get("observationId") or "") == observation and
            marker.get("reviewStatus") == "approved_for_learning")


def _resolve_superseded_feedback(wav_path: Path, request_id: str,
                                 observation: str, *, approved: bool,
                                 revoked: bool) -> dict:
    """Atomically reconcile superseded API responses across *all* revisions.

    Reanalysis and later Reject/Unsure decisions must not strand a pending
    marker or erase a failed remote rollback.  Only a confirmed revocation
    clears a learning-approval marker; failed rollback always blocks learning.
    """
    def update(meta):
        changes = {}
        matched = False
        for key in ("feedbackPending", "supersededFeedbackPending"):
            if _matching_feedback_request(meta.get(key), request_id, observation):
                matched = True
                if revoked:
                    changes[key] = None
                elif approved and key == "feedbackPending":
                    # Convert a stale in-flight marker into an actionable
                    # superseded marker, retaining its request identity.
                    changes["feedbackPending"] = None
                    changes["supersededFeedbackPending"] = meta[key]
        if approved:
            if not revoked:
                # Always persist rollback failure: a newer review revision is
                # *not* proof that an earlier server approval was revoked.
                changes["learningRevocationStatus"] = "ACTION_REQUIRED"
                if meta.get("learningRevocationStatus") != "ACTION_REQUIRED":
                    changes["learningRevocationRequestId"] = request_id
            elif matched:
                other_pending = any(
                    meta.get(key) and key not in changes
                    for key in ("feedbackPending", "supersededFeedbackPending")
                )
                is_unrelated_failure = (
                    meta.get("learningRevocationStatus") == "ACTION_REQUIRED" and
                    str(meta.get("learningRevocationRequestId") or "") != request_id
                )
                # A verified rollback resolves its *own* prior failure marker,
                # never an unrelated manually actionable failure.
                if not other_pending and not is_unrelated_failure:
                    changes["learningRevocationStatus"] = "revoked"
                    changes["learningRevocationRequestId"] = None
        return changes
    return _update_metadata(wav_path, update)


def _metadata_path(wav_path: Path) -> Path:
    return wav_path.with_suffix(".json")


# Serialize metadata read/modify/write in this process. Unique temporary paths
# prevent concurrent writers from clobbering one another's staging files.
_METADATA_LOCKS_GUARD = threading.Lock()
_METADATA_LOCKS: dict[str, threading.RLock] = {}


def _metadata_lock(wav_path: Path) -> threading.RLock:
    key = str(_metadata_path(wav_path).resolve())
    with _METADATA_LOCKS_GUARD:
        return _METADATA_LOCKS.setdefault(key, threading.RLock())


def _load_metadata(wav_path: Path) -> dict:
    p = _metadata_path(wav_path)
    with _metadata_lock(wav_path):
        if not p.exists():
            return {}
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}


def _save_metadata(wav_path: Path, data: dict) -> None:
    p = _metadata_path(wav_path)
    with _metadata_lock(wav_path):
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_name(f"{p.name}.{uuid.uuid4().hex}.tmp")
        try:
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, p)
        finally:
            tmp.unlink(missing_ok=True)


def _update_metadata(wav_path: Path, changes) -> dict:
    """Atomically merge fields with latest metadata, preserving unrelated edits."""
    with _metadata_lock(wav_path):
        current = _load_metadata(wav_path)
        updates = changes(current) if callable(changes) else changes
        current.update(updates)
        _save_metadata(wav_path, current)
        return current


def save_background_audio_review(wav_path: Path, label: str) -> dict:
    """Version a caregiver's environmental label alongside, not inside, evidence."""
    if label not in BACKGROUND_AUDIO_LABELS:
        raise ValueError("Choose a supported background-audio label")
    if not wav_path.is_file():
        raise FileNotFoundError("The original recording no longer exists")

    def changes(current):
        previous = _background_audio_label(current.get("backgroundAudioLabel"))
        if previous == label and current.get("backgroundAudioReviewVersion") == BACKGROUND_AUDIO_REVIEW_VERSION:
            return {}
        history = list(current.get("backgroundAudioReviewHistory") or [])
        history.append({"reviewedAt": datetime.now().isoformat(timespec="seconds"),
                        "previousLabel": previous, "label": label,
                        "reviewSource": "caregiver_explicit", "isAcousticEvidence": False,
                        "speakerIdentityVerified": False})
        return {"backgroundAudioLabel": label,
                "backgroundAudioReviewVersion": BACKGROUND_AUDIO_REVIEW_VERSION,
                "backgroundAudioReviewHistory": history,
                "backgroundAudioIsAcousticEvidence": False,
                "backgroundAudioIsLearningApproval": False}

    return _update_metadata(wav_path, changes)


class DirectRecorder(tk.Tk):
    def __init__(self, initial_tab="record"):
        super().__init__()
        self.title("Hearlium Recording History" if initial_tab == "history" else
                   "Hearlium Parent PC Recording")
        self.geometry("900x720")
        self.minsize(700, 480)

        self.audio_queue: queue.Queue[bytes] = queue.Queue()
        self.stream = None
        self.recording = False
        self.start_time = 0.0
        self.timer_job = None
        self.current_file: Path | None = None
        self._active_recording_path: Path | None = None
        self.last_result: dict | None = None
        self.last_analysis_export: Path | None = None
        self.batch_running = False
        self._analysis_generation = 0
        self._analysis_state_lock = threading.RLock()
        self._analysis_in_flight = False
        self._feedback_in_flight = False
        self._history_cached_rows = []
        # Android keeps suggestions in an analysis export, not inline metadata.
        # Cache verified words by export signature to keep history refresh fast.
        self._history_android_words_cache = {}
        self._history_title_suggestions_cache = {}
        self._history_labels = {}
        self._history_filter_lookup = {"All students": "ALL", "Unassigned": "__UNASSIGNED__"}

        config = _load_parent_pc_config()
        self.api_url = tk.StringVar(value=str(config.get("api_url") or DEFAULT_API_URL))

        self.speaker_id = tk.StringVar(value="")
        self.speaker_role = tk.StringVar(value="Child / student")
        self.counting_mode = tk.BooleanVar(value=False)
        self.context = tk.StringVar()
        self.notes = tk.StringVar()
        self.background_audio = tk.StringVar(value="Not specified")
        self.confirmed_word = tk.StringVar()
        self.status = tk.StringVar(value="Ready")
        self.timer = tk.StringVar(value="00:00")
        self.file_text = tk.StringVar(value="No recording yet")
        self.approval_status = tk.StringVar(value="Not reviewed")

        self._build_ui()
        if initial_tab == "history":
            self.notebook.select(self.history_tab)
        self.refresh_history()

    def _build_ui(self):
        tk.Label(self, text="Hearlium Parent PC Recording",
                 font=("Segoe UI", 22, "bold")).pack(pady=(16, 3))
        tk.Label(self, text="Build 0.4.21 | Branch 2 | Offline Pronunciation and Safe Android Cleanup | 2026-10-28",
                 font=("Segoe UI", 9, "bold"), fg="#174a73").pack(pady=(0, 3))
        tk.Label(
            self,
            text="Record, analyze, review, and approve speech examples for learning.",
            font=("Segoe UI", 10)
        ).pack(pady=(0, 10))

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=14, pady=(4, 12))
        self.notebook = notebook

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

        self.record_content = self._make_scrollable_tab(self.record_tab)
        self._build_record_tab(self.record_content)
        self._build_history_tab(self.history_tab)
        self._build_dashboard_tab(self.dashboard_tab)
        self._build_evidence_tab(self.evidence_tab)
        self._build_analytics_tab(self.analytics_tab)
        self._build_raw_tab(self.raw_tab)
        self._build_connection_tab(self.connection_tab)

    def _make_scrollable_tab(self, tab):
        """Keep lower controls accessible on small screens / high DPI displays."""
        holder = ttk.Frame(tab)
        holder.pack(fill="both", expand=True)
        canvas = tk.Canvas(holder, highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(holder, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        content = ttk.Frame(canvas)
        window_id = canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window_id, width=event.width))
        def scroll(event):
            if canvas.winfo_containing(event.x_root, event.y_root) is not None:
                canvas.yview_scroll(-int(event.delta / 120), "units")
        canvas.bind("<Enter>", lambda event: canvas.bind_all("<MouseWheel>", scroll))
        canvas.bind("<Leave>", lambda event: canvas.unbind_all("<MouseWheel>"))
        return content

    def _build_record_tab(self, parent):
        info = tk.Frame(parent)
        info.pack(fill="x", padx=18, pady=10)

        tk.Label(info, text="Speaker / Student ID:", anchor="w").grid(row=0, column=0, sticky="w")
        tk.Entry(info, textvariable=self.speaker_id, width=32).grid(row=0, column=1, sticky="ew", padx=(10, 0))
        tk.Label(info, text="Speaker category:", anchor="w").grid(row=0, column=2, padx=(12, 4))
        ttk.Combobox(info, textvariable=self.speaker_role, state="readonly", width=17,
                     values=("Child / student", "Adult test / reference")).grid(row=0, column=3, sticky="w")
        tk.Checkbutton(info, text="Counting 1–12 diagnostic (context only)",
                       variable=self.counting_mode).grid(row=3, column=1, sticky="w", pady=(7, 0))

        tk.Label(info, text="Optional context:", anchor="w").grid(row=1, column=0, sticky="w", pady=(8, 0))
        tk.Entry(info, textvariable=self.context, width=48).grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(8, 0))

        tk.Label(info, text="Caregiver / teacher notes:", anchor="w").grid(row=2, column=0, sticky="w", pady=(8, 0))
        tk.Entry(info, textvariable=self.notes, width=48).grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=(8, 0))
        tk.Label(info, text="Background audio (caregiver label):", anchor="w").grid(
            row=4, column=0, sticky="w", pady=(8, 0))
        ttk.Combobox(info, textvariable=self.background_audio, state="readonly", width=30,
                     values=BACKGROUND_AUDIO_LABELS).grid(row=4, column=1, sticky="w", padx=(10, 0), pady=(8, 0))
        tk.Button(info, text="Save Sound Label", command=self.save_sound_label).grid(
            row=4, column=2, columnspan=2, sticky="w", padx=(12, 0), pady=(8, 0))
        tk.Label(info, text="A caregiver observation only — not automatic speaker detection or learning.",
                 fg="#805500").grid(row=5, column=0, columnspan=4, sticky="w", pady=(2, 0))
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

        tk.Label(review, text="What was said? Edit the sentence if needed:").grid(row=0, column=0, sticky="w", padx=10, pady=(8, 3))
        tk.Entry(review, textvariable=self.confirmed_word, width=64).grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=(0, 6))
        tk.Button(review, text="✓ Confirm & Save", command=self.simple_confirm_and_save,
                  font=("Segoe UI", 11, "bold"), bg="#d8efdc").grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        tk.Button(review, text="Not Sure", command=self.simple_unsure).grid(row=2, column=1, sticky="ew", padx=6, pady=5)
        tk.Button(review, text="Reject", command=self.reject_interpretation).grid(row=2, column=2, sticky="ew", padx=6, pady=5)
        tk.Label(review, textvariable=self.approval_status, font=("Segoe UI", 10, "bold")).grid(row=3, column=0, sticky="w", padx=10)
        tk.Button(review, text="Advanced: Review Individual Words", command=self.open_segment_review).grid(
            row=4, column=0, columnspan=3, sticky="w", padx=10, pady=(3, 8))
        tk.Label(review, text="Sentence confirmations are saved as feedback; pronunciation learning requires verified word alignment.",
                 fg="#805500").grid(row=5, column=0, columnspan=3, sticky="w", padx=10, pady=(0, 8))
        review.columnconfigure(0, weight=2)
        review.columnconfigure(1, weight=1)
        review.columnconfigure(2, weight=1)

        bottom = tk.Frame(parent)
        bottom.pack(fill="x", padx=18, pady=(0, 12))
        tk.Button(bottom, text="Open Recording Folder", command=self.open_recording_folder).pack(side="left")
        tk.Button(bottom, text="Clear Results", command=self.clear_results).pack(side="right")

    def _build_history_tab(self, parent):
        top = tk.Frame(parent)
        top.pack(fill="x", padx=12, pady=(8, 4))
        self._history_navigation_buttons = []
        tk.Button(top, text="Refresh", command=self.refresh_history).pack(side="left")
        self.save_suggested_titles_btn = tk.Button(
            top, text="Save Suggested Titles for Existing", command=self.save_suggested_titles_for_existing)
        self.save_suggested_titles_btn.pack(side="left", padx=(8, 4))
        self._history_navigation_buttons.append(self.save_suggested_titles_btn)
        for text, action in (("Play", self.play_selected_history),
                             ("Reanalyze", self.reanalyze_selected),
                             ("Load into Review", self.load_selected_into_review),
                             ("Delete", self.delete_selected_history)):
            btn = tk.Button(top, text=text, command=action)
            btn.pack(side="right" if text == "Delete" else "left", padx=5)
            self._history_navigation_buttons.append(btn)

        filters = tk.LabelFrame(parent, text="Find student recordings")
        filters.pack(fill="x", padx=12, pady=(0, 6))
        self.history_student_filter = tk.StringVar(value="All students")
        self.history_search = tk.StringVar()
        self.history_sort = tk.StringVar(value="Newest first")
        self.history_date_from = tk.StringVar()
        self.history_date_to = tk.StringVar()
        self.history_count = tk.StringVar(value="0 recordings")
        self.history_filter_message = tk.StringVar(
            value="Phone-name upload 2026-10-25c · Type a term and press Search.")

        tk.Label(filters, text="Student:").grid(row=0, column=0, padx=(8, 3), pady=(6, 3), sticky="w")
        self.history_student_combo = ttk.Combobox(filters, textvariable=self.history_student_filter,
                                                  state="readonly", width=30,
                                                  values=("All students", "Unassigned"))
        self.history_student_combo.grid(row=0, column=1, padx=3, pady=(6, 3), sticky="ew")
        tk.Label(filters, text="Search:").grid(row=0, column=2, padx=(8, 3), pady=(6, 3), sticky="w")
        search_controls = tk.Frame(filters)
        search_controls.grid(row=0, column=3, padx=(3, 8), pady=(6, 3), sticky="ew")
        self.history_search_entry = ttk.Entry(search_controls, textvariable=self.history_search, width=28)
        self.history_search_entry.pack(side="left", fill="x", expand=True)
        self.history_search_entry.bind("<Return>", lambda _event: self.execute_history_search())
        tk.Button(search_controls, text="Search", command=self.execute_history_search,
                  font=("Segoe UI", 9, "bold")).pack(side="left", padx=(6, 0))
        tk.Label(filters, text="From (YYYY-MM-DD):").grid(row=1, column=0, padx=(8, 3), pady=3, sticky="w")
        ttk.Entry(filters, textvariable=self.history_date_from, width=16).grid(
            row=1, column=1, padx=3, pady=3, sticky="w")
        tk.Label(filters, text="Through (YYYY-MM-DD):").grid(row=1, column=2, padx=(8, 3), pady=3, sticky="w")
        ttk.Entry(filters, textvariable=self.history_date_to, width=16).grid(
            row=1, column=3, padx=(3, 8), pady=3, sticky="w")
        tk.Label(filters, text="Sort:").grid(row=2, column=0, padx=(8, 3), pady=(3, 8), sticky="w")
        sort_controls = tk.Frame(filters)
        sort_controls.grid(row=2, column=1, padx=3, pady=(3, 5), sticky="ew")
        self.history_sort_combo = ttk.Combobox(
            sort_controls, textvariable=self.history_sort, state="readonly", width=23,
            values=("Newest first", "Oldest first", "Student A–Z", "Student Z–A",
                    "Recording name A–Z", "Recording name Z–A",
                    "Recording title A–Z", "Recording title Z–A",
                    "Speaker ID A–Z", "Speaker ID Z–A",
                    "Review status A–Z", "Review status Z–A",
                    "Word / suggestion A–Z", "Word / suggestion Z–A"))
        self.history_sort_combo.pack(side="left", fill="x", expand=True)
        self.history_sort_combo.bind("<<ComboboxSelected>>", lambda _event: self.execute_history_sort())
        tk.Button(sort_controls, text="Apply Sort", command=self.execute_history_sort).pack(
            side="left", padx=(6, 0))
        tk.Button(filters, text="Clear filters", command=self.clear_history_filters).grid(
            row=2, column=2, padx=3, pady=(3, 8), sticky="w")
        tk.Label(filters, textvariable=self.history_count, font=("Segoe UI", 10, "bold")).grid(
            row=2, column=3, padx=(3, 8), pady=(3, 8), sticky="e")
        tk.Label(filters, textvariable=self.history_filter_message, fg="#805500").grid(
            row=3, column=0, columnspan=4, padx=8, pady=(0, 4), sticky="w")
        filters.columnconfigure(1, weight=1)
        filters.columnconfigure(3, weight=1)
        self.history_student_combo.bind("<<ComboboxSelected>>", lambda _e: self._apply_history_filters())
        for entry in filters.winfo_children():
            if isinstance(entry, ttk.Entry) and entry is not self.history_search_entry:
                entry.bind("<Return>", lambda _event: self.execute_history_search())

        columns = ("date", "student", "title", "speaker", "status", "word", "file")
        history_holder = tk.Frame(parent)
        history_holder.pack(fill="both", expand=True, padx=12, pady=(0, 5))
        history_horizontal = ttk.Scrollbar(history_holder, orient="horizontal")
        history_vertical = ttk.Scrollbar(history_holder, orient="vertical")
        self.history = ttk.Treeview(history_holder, columns=columns, show="headings", selectmode="browse",
                                    xscrollcommand=history_horizontal.set,
                                    yscrollcommand=history_vertical.set)
        self._history_last_sort_heading = None
        self._history_heading_reverse = False
        history_horizontal.configure(command=self.history.xview)
        history_vertical.configure(command=self.history.yview)
        for col, label, width in (("date", "Date", 145), ("student", "Student name", 150),
                                  ("title", "Recording Title / Tag", 260),
                                  ("speaker", "Speaker ID", 150), ("status", "Status", 110),
                                  ("word", "Word / suggestion", 125), ("file", "Recording", 250)):
            self.history.heading(col, text=label,
                                 command=lambda column=col: self.sort_history_by_heading(column))
            self.history.column(col, width=width, anchor="w")
        history_vertical.pack(side="right", fill="y")
        history_horizontal.pack(side="bottom", fill="x")
        self.history.pack(fill="both", expand=True)

        identity = tk.Frame(parent)
        identity.pack(fill="x", padx=12, pady=(0, 6))
        self.name_selected_btn = tk.Button(identity, text="Set student name for selected ID",
                                           command=self.name_selected_student)
        self.name_selected_btn.pack(side="left")
        self._history_navigation_buttons.append(self.name_selected_btn)
        tk.Label(identity, text="Labels do not change speaker IDs, recordings, or learning evidence.",
                 fg="#805500").pack(side="left", padx=(8, 0))

        label_frame = tk.LabelFrame(parent, text="Recording title and searchable tags (separate from audio/evidence)")
        label_frame.pack(fill="x", padx=12, pady=(0, 6))
        self.history_custom_title = tk.StringVar()
        self.history_custom_tags = tk.StringVar()
        self.history_custom_notes = tk.StringVar()
        self.history_suggested_title = tk.StringVar(value="Select a recording to see its suggested title.")
        tk.Label(label_frame, text="Title:").grid(row=0, column=0, padx=(8, 3), pady=2, sticky="w")
        ttk.Entry(label_frame, textvariable=self.history_custom_title, width=38).grid(
            row=0, column=1, columnspan=3, padx=3, pady=2, sticky="ew")
        tk.Button(label_frame, text="Save Label", command=self.save_selected_recording_label).grid(
            row=0, column=4, padx=4, pady=2, sticky="w")
        tk.Button(label_frame, text="Use Suggested", command=self.use_suggested_recording_title).grid(
            row=0, column=5, padx=4, pady=2, sticky="w")
        tk.Label(label_frame, text="Tags:").grid(row=1, column=0, padx=(8, 3), pady=2, sticky="w")
        ttk.Entry(label_frame, textvariable=self.history_custom_tags, width=30).grid(
            row=1, column=1, columnspan=2, padx=3, pady=2, sticky="ew")
        tk.Label(label_frame, text="Notes:").grid(row=1, column=3, padx=(8, 3), pady=2, sticky="w")
        ttk.Entry(label_frame, textvariable=self.history_custom_notes, width=30).grid(
            row=1, column=4, columnspan=2, padx=3, pady=2, sticky="ew")
        tk.Label(label_frame, textvariable=self.history_suggested_title, fg="#805500",
                 wraplength=680, justify="left").grid(row=2, column=0, columnspan=6, padx=8, sticky="w")
        label_frame.columnconfigure(1, weight=1)
        label_frame.columnconfigure(4, weight=1)

        notes_frame = tk.LabelFrame(parent, text="Selected recording details (read-only evidence context)")
        notes_frame.pack(fill="x", padx=12, pady=(0, 12))
        self.history_details = tk.Text(notes_frame, height=4, wrap="word")
        self.history_details.pack(fill="x", padx=8, pady=8)
        self.history.bind("<<TreeviewSelect>>", lambda _e: self.show_history_details())

    def clear_history_filters(self):
        self.history_student_filter.set("All students")
        self.history_search.set("")
        self.history_sort.set("Newest first")
        self.history_date_from.set("")
        self.history_date_to.set("")
        self.refresh_history()

    def execute_history_search(self):
        """Explicit Search button/Enter: reload current saved labels and filter."""
        self.refresh_history()

    def execute_history_sort(self):
        """Explicit Apply Sort button as well as combobox selection."""
        self._apply_history_filters()

    def sort_history_by_heading(self, column: str):
        """A heading click sorts the column; a second click reverses it."""
        modes = {
            "date": ("Newest first", "Oldest first"),
            "student": ("Student A–Z", "Student Z–A"),
            "title": ("Recording title A–Z", "Recording title Z–A"),
            "speaker": ("Speaker ID A–Z", "Speaker ID Z–A"),
            "status": ("Review status A–Z", "Review status Z–A"),
            "word": ("Word / suggestion A–Z", "Word / suggestion Z–A"),
            "file": ("Recording name A–Z", "Recording name Z–A"),
        }
        if column not in modes:
            return
        self._history_heading_reverse = (
            not self._history_heading_reverse if self._history_last_sort_heading == column else False)
        self._history_last_sort_heading = column
        self.history_sort.set(modes[column][int(self._history_heading_reverse)])
        self.execute_history_sort()

    def name_selected_student(self):
        if not self._ensure_not_recording():
            return
        wav_path = self._selected_history_path()
        if not wav_path:
            return
        meta = _load_metadata(wav_path)
        speaker_id = str(meta.get("speakerId") or "").strip()
        if is_unassigned(speaker_id):
            messagebox.showwarning("Student name", "This recording has no unique student ID.\n\n"
                                   "Do not assign a name to a shared/unknown ID; that could label another student's recordings."
                                   " Use a unique speaker ID for future recordings.")
            return
        profiles = load_profiles(STUDENT_PROFILES_PATH)
        old_name = student_display_name(speaker_id, meta, profiles)
        new_name = simpledialog.askstring("Name this student", "Display name for speaker ID:\n" + speaker_id +
                                          "\n\nThis will label all recordings with this ID.",
                                          initialvalue=old_name, parent=self)
        if new_name is None:
            return
        count = sum(row.get('speakerId') == speaker_id for row in self._history_cached_rows)
        if not messagebox.askyesno("Confirm student name", f"Show '{new_name.strip()}' for {count} recording(s) "
                                 f"with speaker ID {speaker_id}?\n\n"
                                 "Only proceed if every recording with this ID belongs to the same student. "
                                 "Shared Android devices may use one ID for different students.\n\n"
                                 "The audio, recording metadata, and evidence will not change."):
            return
        try:
            assign_display_name(STUDENT_PROFILES_PATH, STUDENT_PROFILE_AUDIT_PATH, speaker_id, new_name)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Student name", f"Could not save the display name: {exc}")
            return
        self.refresh_history()

    def _apply_history_filters(self):
        if not hasattr(self, "history"):
            return
        label = self.history_student_filter.get()
        selected_id = self._history_filter_lookup.get(label, "ALL")
        try:
            filtered = filter_and_sort(
                self._history_cached_rows, speaker_id=selected_id,
                search=self.history_search.get(), date_from=self.history_date_from.get(),
                date_to=self.history_date_to.get(), sort_by=self.history_sort.get())
        except ValueError as exc:
            self.history_filter_message.set(str(exc))
            self.history_count.set("Check date format")
            return
        previous = self._selected_history_path_silent()
        for item in self.history.get_children():
            self.history.delete(item)
        for row in filtered:
            self.history.insert("", "end", iid=str(row['path']), values=(
                row['created'], row['displayName'], row['title'], row['speakerId'], row['status'],
                row['word'], row['filename']))
        if previous and str(previous) in self.history.get_children():
            self.history.selection_set(str(previous))
        else:
            self.history_details.delete("1.0", "end")
            self._clear_selected_history_label_fields()
        self.history_count.set(f"{len(filtered)} of {len(self._history_cached_rows)} recordings")
        term = self.history_search.get().strip()
        self.history_filter_message.set(
            "Phone-name upload 2026-10-25c · " +
            (f"Search: '{term}' · " if term else "") +
            f"Sorted by: {self.history_sort.get()}" +
            (" · No matches" if not filtered else ""))
        self.history.yview_moveto(0)

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
        tk.Button(toolbar, text="Align Confirmed Words", command=self.align_confirmed_words).pack(side="left", padx=6)
        self.evidence_box = tk.Text(parent, wrap="word")
        self.evidence_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.evidence_box.insert("1.0", "Evidence will appear here after analysis.\n\n"
                                 "Original observations remain immutable; interpretation is separate.")

    def align_confirmed_words(self):
        wav = self.current_file
        if not wav or not Path(wav).is_file():
            messagebox.showinfo("Choose a recording", "Load a saved recording first.", parent=self)
            return
        suggested = ((self.last_result or {}).get('wordRecognition') or {}).get('text', '')
        reference = simpledialog.askstring(
            "Align Confirmed Words",
            "After listening, enter the exact words you heard.\n"
            "OK confirms this text for timing only. It does not approve learning.\n"
            "The original recording and recognition results are preserved.",
            initialvalue=suggested, parent=self)
        if not reference or not reference.strip():
            return
        destination = ANALYSIS_RESULTS_DIR / 'phoneme_alignment_reports' / ('alignment_' + uuid.uuid4().hex + '.json')
        self.status.set('Aligning confirmed words...')
        def worker():
            import subprocess
            import sys
            import hashlib
            arguments = ['--align-phonemes', str(wav), '--reference', reference,
                         '--confirmed', '--output', str(destination)]
            command = ([sys.executable] + arguments if getattr(sys, 'frozen', False)
                       else [sys.executable, str(Path(__file__).with_name('hearlium_launcher.py'))] + arguments)
            try:
                original = hashlib.sha256(Path(wav).read_bytes()).hexdigest()
                process = subprocess.run(command, timeout=120, capture_output=True,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                if process.returncode:
                    error = destination.with_suffix('.error.json')
                    detail = json.loads(error.read_text(encoding='utf-8'))['error'] if error.exists() else 'Alignment process failed'
                    raise RuntimeError(detail)
                report = json.loads(destination.read_text(encoding='utf-8'))
                if report.get('originalSha256VerifiedAfterAlignment') != original:
                    raise RuntimeError('Alignment report does not match the selected audio')
            except Exception as exc:
                self.after(0, lambda detail=str(exc): messagebox.showerror('Alignment unavailable', detail, parent=self))
                self.after(0, lambda: self.status.set('Alignment failed; original recording preserved.'))
                return
            self.after(0, lambda: self._show_alignment_report(report, destination))
        threading.Thread(target=worker, daemon=True).start()

    def _show_alignment_report(self, report, destination):
        popup = tk.Toplevel(self)
        popup.title('Confirmed-word alignment — review only')
        popup.geometry('850x600')
        tk.Label(popup, text='Transcript-constrained timing; not proof of pronunciation. No learning was approved.',
                 wraplength=800).pack(padx=12, pady=8)
        text = tk.Text(popup, wrap='word')
        text.pack(fill='both', expand=True, padx=12, pady=8)
        lines = [report.get('referenceText', ''), '',
                 'Expected word / proposed seconds / model sound labels', '']
        for word in report.get('words', []):
            lines.append(f"{word['referenceWord']}   {word['startSeconds']:.2f}–{word['endSeconds']:.2f}s")
            lines.append('  ' + '  '.join(
                f"{phone['phone']} {phone['startSeconds']:.2f}–{phone['endSeconds']:.2f}"
                for phone in word.get('phones', [])))
        text.insert('1.0', '\n'.join(lines))
        text.config(state='disabled')
        tk.Label(popup, text=str(destination), wraplength=800).pack(padx=12, pady=8)
        self.status.set('Separate phoneme alignment report saved.')

    def _build_analytics_tab(self, parent):
        controls = tk.Frame(parent)
        controls.pack(fill="x", padx=12, pady=10)
        tk.Button(controls, text="Batch Folder", command=self.choose_batch_folder).pack(side="left")
        tk.Button(controls, text="Rebuild Analytics", command=self.rebuild_analytics).pack(side="left", padx=6)
        tk.Button(controls, text="Open Analysis Results", command=self.open_analysis_results_folder).pack(side="left", padx=6)
        tk.Button(controls, text="Integrity Reports", command=self.open_integrity_reports).pack(side="left", padx=6)

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
                write_event("recorder_api_connection_test", outcome="success", httpStatus=response.status_code)
                msg = (
                    f"Connected • API {data.get('apiVersion','')} • "
                    f"model={data.get('model','')} • device={data.get('device','')}"
                )
                self.after(0, lambda: self.connection_status.set(msg))
            except Exception as exc:
                response = getattr(exc, "response", None)
                write_event("recorder_api_connection_test", outcome="failed",
                            errorType=type(exc).__name__,
                            httpStatus=getattr(response, "status_code", None))
                error_text = str(exc)
                self.after(0, lambda message=error_text: self.connection_status.set(f"Connection failed: {message}"))

        threading.Thread(target=worker, daemon=True).start()

    def refresh_dashboard(self):
        result = self.last_result
        if not isinstance(result, dict):
            self.dashboard_box.delete("1.0", "end")
            self.dashboard_box.insert("1.0", "Analyze or load a recording to populate the AI Dashboard.")
            return

        analysis = result.get("analysis") or {}
        candidates = result.get("candidates") or []
        word_recognition = result.get("wordRecognition") or {}
        word_text = str(word_recognition.get("text") or "").strip()
        word_valid = word_recognition.get("status") == "candidate_transcription" and bool(word_text)
        lines = [
            "POSSIBLE SPOKEN WORDS: " + (word_text if word_valid else "Unavailable — listen to saved audio"),
            "Unverified AI suggestion; caregiver confirmation required.",
        ]
        lines.extend(_phoneme_review_warning_lines(result))
        lines.extend(_recognition_diagnostic_lines(result))
        source_review = result.get("speakerSourceReview") or {}
        if isinstance(source_review, dict) and source_review.get("targetSpeakerIdentityVerified") is False:
            lines.append("TARGET SPEAKER ISOLATION: NOT VERIFIED — background singing or other voices may be present.")
        silero = result.get("sileroVAD") or {}
        if isinstance(silero, dict):
            lines.append(
                "SILERO VAD (independent Layer 2 speech activity): "
                + str(silero.get("status", "not available"))
                + " — does NOT identify the child or distinguish TV voices."
            )
            if silero.get("status") == "evaluated":
                lines.append(
                    f"Silero detected {silero.get('speechSegmentCount', 0)} candidate speech region(s); "
                    "all require speaker review."
                )
        candidate_review = result.get("speechActivityCandidateReview") or {}
        if candidate_review.get("status") == "evaluated_review_only":
            lines.append(
                f"BACKGROUND PHONEME REVIEW: {candidate_review.get('outsideActivitySegmentCount', 0)} "
                "segment(s) outside Silero activity withheld from ordinary word suggestions. "
                "All original evidence and alternative candidates remain available; "
                "quiet target speech may require manual review."
            )
        word_activity = result.get("wordAsrActivityReview") or {}
        if word_activity.get("outsideActivitySegmentCount", 0):
            snippets = ", ".join(repr(x) for x in
                                 (word_activity.get("outsideActivityTextFragments") or [])[:3])
            lines.append(
                "WORD RECOGNITION / SILERO WARNING: "
                f"{word_activity.get('outsideActivitySegmentCount')} ASR segment(s) "
                "outside independently detected candidate voice activity; "
                f"review {snippets or 'timestamps'} in original audio. "
                "Words are NOT deleted and Silero cannot prove silence."
            )
        elif word_activity.get("overlongSpanningSegmentCount", 0):
            lines.append(
                "WORD RECOGNITION TIMING REVIEW: "
                f"{word_activity.get('overlongSpanningSegmentCount')} long ASR segment(s) "
                "span quiet intervals; individual word timings are unverified."
            )
        quality_windows = result.get("speechWindowQualityReview") or {}
        if quality_windows.get("status") == "evaluated_review_only":
            lines.append(
                "CANDIDATE-ACTIVITY WINDOW QUALITY (NOT SPEAKER VERIFIED): "
                f"peak={quality_windows.get('activityWindowPeakRatio')}; "
                f"RMS={quality_windows.get('activityWindowRmsRatio')}; "
                "whole-session quality unchanged."
            )
            if quality_windows.get("sessionSilenceMayReflectIntentionalPauses"):
                lines.append(
                    "LONG-PAUSE QUALITY REVIEW: the whole-session poor/silence "
                    "rating may reflect deliberate gaps; window metrics are "
                    "not verified target-speech quality."
                )
        disagreement = result.get("recognizerDisagreementReview") or {}
        if disagreement.get("warningCodes"):
            lines.append(
                "INDEPENDENT ENGINE DISAGREEMENT: "
                + " ".join((disagreement.get("warningsForCaregiver") or
                            disagreement["warningCodes"])[:6])
                + " All hypotheses require caregiver review."
            )
        utterance_rate = result.get("utteranceProsodyReview") or {}
        if utterance_rate.get("status") == "review_only":
            lines.append(
                "PROVISIONAL WITHIN-UTTERANCE RATE: "
                f"{utterance_rate.get('withinUtteranceSyllablesPerSecond')} energy peaks/sec (not verified syllables) "
                f"({utterance_rate.get('withinUtteranceRateBand')}); "
                "intentional long gaps excluded, speaker identity unverified."
            )
        lines.extend([
            "RAW PHONEME OUTPUT (preview only, NOT a word transcript): "
            + _raw_phoneme_preview(result.get('transcript', '—')),
            f"OVERALL HEURISTIC CANDIDATE SCORE: {analysis.get('overallConfidence', '—')}",
            f"UNCERTAINTY: {analysis.get('uncertaintyBand', '—')}",
            f"FINAL-CONSONANT CANDIDATE FLAG (not verified): {analysis.get('possibleFinalConsonantOmission', False)}",
            f"INITIAL-CONSONANT CANDIDATE FLAG (not verified): {analysis.get('possibleInitialConsonantOmission', False)}",
            "",
            "TOP CANDIDATES",
        ])
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
            self.evidence_box.delete("1.0", "end")
            self.evidence_box.insert("1.0", "No analysis evidence loaded for this recording.")
            return

        analysis = result.get("analysis") or {}
        evidence = analysis.get("evidence") or {}
        acoustic = evidence.get("acoustic") or {}
        temporal = evidence.get("temporal") or {}
        observation = result.get("observation") or {}
        phoneme = result.get("phonemeAnalysis") or {}
        learning = analysis.get("learningLayers") or {}
        speech_review = result.get("speechActivityReview") or {}
        silero = result.get("sileroVAD") or {}
        phoneme_timing_review = result.get("phonemeTimingReview") or {}
        source_review = result.get("speakerSourceReview") or {}
        word_activity = result.get("wordAsrActivityReview") or {}
        quality_windows = result.get("speechWindowQualityReview") or {}
        disagreement = result.get("recognizerDisagreementReview") or {}
        loaded_wav = getattr(self, "current_file", None)
        background_label = (_background_audio_label(_load_metadata(loaded_wav).get("backgroundAudioLabel"))
                            if isinstance(loaded_wav, Path) and loaded_wav.is_file()
                            else "Not specified")

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
            f"Estimated last sound activity: {acoustic.get('estimatedActivityEndSeconds','—')} sec",
            f"Estimated trailing quiet: {acoustic.get('trailingQuietSeconds','—')} sec",
            f"Activity-tail energy ratio: {acoustic.get('activityTailEnergyRatio','—')}",
            f"Activity estimate: {acoustic.get('activityEstimationStatus','not measured')}",
            f"Last detected energy activity: {acoustic.get('lastDetectedEnergyActivitySeconds','—')} sec",
            f"Separate activity islands: {acoustic.get('activityIslandCount','—')}",
            f"Weak late sound candidates: {acoustic.get('weakLateActivityIslandCount','—')}",
            f"Ambiguous separate activity islands: {acoustic.get('ambiguousActivityIslandCount','—')}",
            "If the estimate is ambiguous, no activity endpoint or trailing quiet is asserted.",
            "Activity is an energy estimate, NOT verified speech or proof of a missing consonant.",
            "",
            "TEMPORAL EVIDENCE",
            f"Tail change: {temporal.get('tailChange','—')}",
            f"Tail window: {temporal.get('tailWindowMs','—')} ms",
            f"Activity-tail change: {temporal.get('activityTailChange','—')}",
            f"Activity-tail window: {temporal.get('activityTailWindowMs','—')} ms",
            "",
            "SPEECH VERSUS AMBIENT SOUND — UNVERIFIED REVIEW",
            f"Cross-check status: {speech_review.get('status','not available')}",
            f"Word recognizer candidate end: {speech_review.get('wordAsrEndSeconds','—')} sec",
            f"Phoneme candidate end: {speech_review.get('phonemeCandidateEndSeconds','—')} sec",
            f"Independent recognizer disagreement: {speech_review.get('endDisagreementSeconds','—')} sec",
            f"Possible late sound after word hypothesis: {speech_review.get('possibleLateSoundBeyondWordAsrSeconds','—')} sec",
            f"Unverified candidate speech end: {speech_review.get('candidateSpeechEndSeconds','—')} sec",
            "Late sound is NOT proven ambient noise; only the caregiver can confirm.",
            "Review-only interpretation. Original acoustic observations and learning remain unchanged.",
            "",
            "SILERO VAD — INDEPENDENT LAYER 2 SPEECH-ACTIVITY VIEW",
            f"Model inference status: {silero.get('status', 'not available')}",
            f"Model package version: {silero.get('modelPackageVersion', 'not available')}",
            f"Candidate speech region count: {silero.get('speechSegmentCount', 'not available')}",
            f"Total candidate speech duration: {silero.get('speechDurationSeconds', 'not available')} sec",
            f"Last candidate speech end: {silero.get('lastDetectedSpeechSeconds', 'not available')} sec",
            f"Silero/word hypothesis end disagreement: {speech_review.get('sileroWordAsrEndDisagreementSeconds', '—')} sec",
            "VAD detects voices, INCLUDING television dialogue or singing; not target-speaker identity.",
            "A VAD region or ASR/VAD agreement never authorizes word learning or phoneme-error findings.",
            *[
                f"  Candidate speech interval: {item.get('startSeconds')}–{item.get('endSeconds')} sec"
                for item in (silero.get('speechSegments') or [])[:20]
                if isinstance(item, dict)
            ],
            "",
            "WORD-ASR TIMESTAMP VERSUS SILERO — UNVERIFIED",
            f"Word-ASR crosscheck status: {word_activity.get('status', 'not available')}",
            f"ASR segments outside Silero activity: {word_activity.get('outsideActivitySegmentCount', '—')}",
            f"Overlong ASR segments spanning quiet intervals: {word_activity.get('overlongSpanningSegmentCount', '—')}",
            f"Outside-activity words requiring listening: {word_activity.get('outsideActivityTextFragments', [])}",
            "This is a segment timing crosscheck, NOT word-level alignment or verified absence of speech.",
            "All original word hypotheses remain available for caregiver review.",
            "",
            "SPEECH-WINDOW SIGNAL QUALITY — REVIEW ONLY",
            f"Whole-session quality label (unchanged): {quality_windows.get('wholeSessionQualityLabel', '—')}",
            f"Candidate window total duration: {quality_windows.get('candidateWindowDurationSeconds', '—')} sec",
            f"Candidate window peak: {quality_windows.get('activityWindowPeakRatio', '—')}",
            f"Candidate window RMS: {quality_windows.get('activityWindowRmsRatio', '—')}",
            f"Whole-session silence may include intentional pauses: {quality_windows.get('sessionSilenceMayReflectIntentionalPauses', '—')}",
            "Silero cannot isolate the child or prove these are clean, intelligible speech windows.",
            "",
            "INDEPENDENT RECOGNIZER DISAGREEMENT — REVIEW ONLY",
            f"Crosscheck status: {disagreement.get('status', 'not available')}",
            f"Reasons: {disagreement.get('warningsForCaregiver', [])}",
            "Model agreement is not verified accuracy, and cannot approve learning.",
            "",
            "TARGET SPEAKER AND BACKGROUND VOCAL SOURCES — REVIEW ONLY",
            f"Attribution status: {source_review.get('status','not evaluated')}",
            f"Target speaker identity verified: {source_review.get('targetSpeakerIdentityVerified',False)}",
            f"Caregiver-labeled background audio: {background_label}",
            "Background singing can be genuine vocal activity but must NOT be assigned to the student.",
            "Caregiver label is review metadata, not measured sound evidence or learning approval.",
            "",
            "LAYER 2/3 — PHONEME TIMING RELIABILITY REVIEW",
            f"Review status: {phoneme_timing_review.get('status','not available')}",
            f"Possible overlong word segment: {phoneme_timing_review.get('extendedWordSegmentNeedsReview','—')}",
            f"Uncorroborated late CTC segments: {phoneme_timing_review.get('uncorroboratedLateSegmentCount','—')}",
            f"Automatic word suggestions on hold: {phoneme_timing_review.get('automaticWordSuggestionHoldCount','—')}",
            f"Loudest sound window begins: {phoneme_timing_review.get('loudestSoundWindowStartSeconds','—')} sec",
            f"Legacy fixed-3-sec energy comparison (may include target words): {phoneme_timing_review.get('lateToEarlyPeakWindowRmsRatio','—')}",
            f"After/between word-ASR energy comparison (UNVERIFIED boundary): {phoneme_timing_review.get('postWordToDuringWordPeakRmsRatio','—')}",
            "Late phonemes remain in original CTC evidence; automatic word guesses may be withheld.",
            "Sound energy does not establish speech, singing, or speaker identity. Human review is required.",
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
                result = analyze_saved_wav(
                    self.api_base(), wav_path,
                    {"context": self.context.get().strip(),
                     "speaker_id": self.speaker_id.get().strip() or "anonymous",
                     "session_id": str(uuid.uuid4()),
                     "recording_id": wav_path.stem},
                    progress=lambda stage: self.after(0, self.status.set, stage))
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

    def open_integrity_reports(self):
        folder = ANALYSIS_RESULTS_DIR / "integrity_reports"
        folder.mkdir(parents=True, exist_ok=True)
        os.startfile(str(folder))

    def _set_history_navigation_enabled(self, enabled: bool) -> None:
        for btn in getattr(self, "_history_navigation_buttons", []):
            btn.config(state="normal" if enabled else "disabled")

    def _ensure_not_recording(self) -> bool:
        if self.recording:
            messagebox.showinfo("Finish recording", "Please tap Stop before loading, reanalyzing, or deleting a recording.")
            return False
        return True

    def save_sound_label(self):
        if not self._ensure_not_recording():
            return
        if self.current_file is None or not self.current_file.is_file():
            messagebox.showinfo("Background audio", "First record or load a saved WAV.")
            return
        try:
            save_background_audio_review(self.current_file, self.background_audio.get())
        except (OSError, ValueError) as exc:
            messagebox.showerror("Background audio", f"Label was not saved: {exc}")
            return
        self.status.set("Caregiver background-audio label saved separately from acoustic evidence")
        self.refresh_evidence()
        self.refresh_history()

    def start_recording(self):
        if self.recording:
            return
        speaker = self.speaker_id.get().strip()
        if not speaker or speaker.lower() in ("anonymous", "student-1"):
            if not messagebox.askyesno("Confirm speaker", "Speaker ID is blank or the shared test ID 'student-1'.\n\nRecord under this ID anyway?\n\nUse a different ID for each child and for adult tests."):
                return
        speaker = speaker or "anonymous"
        self._recording_speaker_id = speaker
        self._recording_speaker_role = self.speaker_role.get()
        self._recording_counting_mode = self.counting_mode.get()
        self.background_audio.set("Not specified")
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in speaker)
        # Microsecond timestamp plus random token avoids collisions between
        # rapid recordings or multiple application instances.
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        target = RECORDINGS_DIR / f"{safe}_{stamp}_{uuid.uuid4().hex[:8]}.wav"
        old_file = self.current_file
        self._clear_loaded_analysis()
        self._active_recording_path = target
        self.current_file = target

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
            self._active_recording_path = None
            self.current_file = old_file
            messagebox.showerror("Microphone error", f"Could not start the microphone.\n\n{exc}")
            return

        self.recording = True
        self._set_history_navigation_enabled(False)
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
        # Save to the path captured at recording start, never mutable current_file.
        recording_file = self._active_recording_path
        self._set_history_navigation_enabled(True)
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

        self._active_recording_path = None
        if not chunks or recording_file is None:
            self.status.set("No audio captured")
            self.record_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            return

        try:
            # Exclusive creation ensures an existing WAV is NEVER truncated.
            with recording_file.open("xb") as raw:
                with wave.open(raw, "wb") as wav:
                    wav.setnchannels(CHANNELS)
                    wav.setsampwidth(2)
                    wav.setframerate(SAMPLE_RATE)
                    wav.writeframes(b"".join(chunks))
        except Exception as exc:
            self.status.set("Recording could not be saved")
            self.record_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            messagebox.showerror("Recording save failed", f"Original recordings were not overwritten.\n\n{exc}")
            return

        elapsed = int(time.monotonic() - self.start_time)
        meta = {
            "speakerId": getattr(self, "_recording_speaker_id", "anonymous"),
            "source": "parent_pc",
            "speakerRole": getattr(self, "_recording_speaker_role", "Child / student"),
            "countingDiagnostic": getattr(self, "_recording_counting_mode", False),
            "context": self.context.get().strip(),
            "notes": self.notes.get().strip(),
            "backgroundAudioLabel": "Not specified",
            "createdAt": datetime.now().isoformat(timespec="seconds"),
            "durationSeconds": elapsed,
            "reviewStatus": "not_reviewed",
            "recordingFile": recording_file.name,
        }
        try:
            # Identify the finalized original before its first API analysis.
            # The worker then uses protected saved-WAV analysis from the first
            # click, so the API cannot create a parent_pc_api_ audio duplicate.
            meta.update(capture_identity(recording_file))
            _save_metadata(recording_file, meta)
            metadata_saved = True
        except Exception as exc:
            metadata_saved = False
            messagebox.showerror(
                "Recording details could not be saved",
                f"The original audio was saved at:\n{recording_file}\n\n"
                f"Its student details could not be saved: {exc}"
            )

        self.status.set("Recording saved" if metadata_saved else "Audio saved; recording details need attention")
        self.timer.set(f"{elapsed // 60:02d}:{elapsed % 60:02d}")
        self.current_file = recording_file
        self.file_text.set(str(recording_file))
        self.record_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.analyze_btn.config(state="normal" if metadata_saved else "disabled")
        self.play_btn.config(state="normal")
        self.refresh_history()

    def analyze_recording(self):
        if self.recording:
            messagebox.showinfo("Finish recording", "Please tap Stop before analyzing a recording.")
            return
        if getattr(self, "_feedback_in_flight", False):
            messagebox.showinfo("Caregiver feedback pending", (
                "A caregiver decision is still being saved or reconciled. "
                "Finish that request before reanalyzing this recording."))
            return
        if not self.current_file or not self.current_file.exists():
            messagebox.showinfo("Analyze Recording", "Record or load a speech sample first.")
            return
        self._clear_loaded_analysis()
        self._analysis_in_flight = True
        self.analyze_btn.config(state="disabled")
        self.approval_status.set("Analysis in progress — review unavailable")
        self.status.set("Analyzing…")
        threading.Thread(target=self._analyze_worker, args=(self.current_file, self._analysis_generation), daemon=True).start()

    def _analysis_request_is_current(self, wav_path: Path, generation: int) -> bool:
        return self.current_file == wav_path and generation == self._analysis_generation

    def _analysis_progress(self, wav_path: Path, generation: int, stage: str):
        if self._analysis_request_is_current(wav_path, generation):
            self.status.set(stage)

    def _commit_analysis_if_current(self, wav_path: Path, generation: int, result: dict,
                                    speaker: str, context: str, session_id: str):
        """Reject stale results *before* metadata or exports can be overwritten.

        A new immutable versioned export is written first. Metadata then points
        to that version; the legacy latest-export mirror is updated last. This
        order prevents a failed metadata save from publishing a wrong analysis.
        """
        with self._analysis_state_lock:
            if not self._analysis_request_is_current(wav_path, generation):
                write_event("stale_recording_analysis_ignored", stage="before_persist")
                return None
            if not wav_path.is_file():
                raise FileNotFoundError("The analyzed recording was deleted before results could be saved")
            obs_id = observation_id(result)
            if not obs_id:
                raise ValueError("Analysis returned no observation ID; refusing to replace review evidence")
            candidates = result.get("candidates") or []
            best_word = (str(candidates[0].get("word") or candidates[0].get("candidate") or "")
                         if candidates and isinstance(candidates[0], dict) else "")
            recording_id = str(result.get("recordingId") or wav_path.stem)
            version_file = ANALYSIS_RESULTS_DIR / f"{wav_path.stem}_analysis_{uuid.uuid4().hex}.json"
            with _metadata_lock(wav_path):
                if not self._analysis_request_is_current(wav_path, generation):
                    write_event("stale_recording_analysis_ignored", stage="before_metadata")
                    return None
                old_meta = _load_metadata(wav_path)
                old_obs = str(old_meta.get("observationId") or "").strip()
                # Store each prior caregiver decision with its original observation.
                updates = {
                    "speakerId": speaker, "context": context or "",
                    "analysisResult": result, "observationId": obs_id,
                    "recordingId": recording_id,
                    "sessionId": result.get("sessionId") or session_id,
                    "bestCandidate": best_word,
                    "analyzedAt": datetime.now().isoformat(timespec="seconds"),
                    "analysisExport": version_file.name,
                }
                if old_obs and old_obs != obs_id:
                    previous = list(old_meta.get("previousAnalysisReviews") or [])
                    if (old_meta.get("reviewStatus") not in (None, "", "not_reviewed")
                            or old_meta.get("learningFeedback")):
                        previous.append({"observationId": old_obs,
                                         "reviewStatus": old_meta.get("reviewStatus"),
                                         "reviewedAt": old_meta.get("reviewedAt"),
                                         "confirmedWord": old_meta.get("confirmedWord"),
                                         "learningFeedback": old_meta.get("learningFeedback")})
                    updates.update({"previousAnalysisReviews": previous,
                                    "reviewStatus": "not_reviewed", "reviewedAt": "",
                                    "confirmedWord": "", "learningFeedback": None})
                # Versioned export stays immutable and is retained for audit.
                _write_analysis_export(wav_path, result, destination=version_file)
                try:
                    _update_metadata(wav_path, updates)
                except Exception:
                    version_file.unlink(missing_ok=True)
                    raise
                # A legacy latest-export mirror is maintained for Analytics & Batch.
                # Failing to update that *derived* copy must not undo committed evidence.
                try:
                    _write_analysis_export(wav_path, result)
                except OSError as exc:
                    write_event("analysis_export_mirror_failed", errorType=type(exc).__name__)
            return version_file

    def _analyze_worker(self, wav_path: Path, generation: int, reanalysis=False):
        meta = _load_metadata(wav_path)
        speaker = meta.get("speakerId") or "anonymous"
        context = meta.get("context") or ""
        session_id = str(uuid.uuid4())
        recording_id = str(meta.get("recordingId") or wav_path.stem)
        # Opening Android history on the PC does not change its origin.
        source = "android" if meta.get("source") == "android" else "parent_pc"
        # Saved recordings use protected reanalysis from either PC button.
        reanalysis = bool(reanalysis or source == "android" or meta.get("observationId")
                          or (meta.get("recordingId") and meta.get("audioSha256")))
        try:
            before = integrity_snapshot(wav_path.parent) if reanalysis else None
            if before is not None and wav_path.name not in before:
                raise RuntimeError("Cannot verify the original WAV; reanalysis was not sent.")
            request_succeeded = False
            try:
                result = analyze_saved_wav(
                    self.api_base(), wav_path,
                    {"context": context, "speaker_id": speaker,
                     "session_id": session_id, "recording_id": recording_id,
                     "recording_source": source, "reanalysis": "true" if reanalysis else "false"},
                    progress=lambda stage: self.after(0, self._analysis_progress, wav_path, generation, stage))
                request_succeeded = True
            finally:
                if before is not None:
                    report_path, passed = save_integrity_report(
                        ANALYSIS_RESULTS_DIR / "integrity_reports", before,
                        integrity_snapshot(wav_path.parent), wav_path, request_succeeded)
                    if not passed:
                        raise RuntimeError(f"WAV integrity check failed. Review is blocked. Report: {report_path}")
            if before is not None:
                result = dict(result)
                result["reanalysisIntegrity"] = {"wavIntegrityPassed": True, "reportPath": str(report_path)}
            export_path = self._commit_analysis_if_current(wav_path, generation, result, speaker, context, session_id)
            if export_path is not None:
                self.after(0, self._apply_analysis_result, wav_path, generation, result, export_path)
        except Exception as exc:
            error_text = str(exc)
            self.after(0, self._apply_analysis_error, wav_path, generation, error_text)

    def _apply_analysis_result(self, wav_path: Path, generation: int, result: dict, export: Path):
        """Never put a late analysis result onto another recording's review screen."""
        self.refresh_history()
        if self.current_file != wav_path or generation != self._analysis_generation:
            write_event("stale_recording_analysis_ignored")
            return
        self._analysis_in_flight = False
        self.last_result = result
        self.last_analysis_export = export
        self._show_result(result)
        self.refresh_dashboard()
        self.refresh_evidence()
        self.refresh_raw_json()
        self.rebuild_analytics()

    def _apply_analysis_error(self, wav_path: Path, generation: int, error_text: str):
        if self._analysis_request_is_current(wav_path, generation):
            self._analysis_in_flight = False
            self._show_error(error_text)

    def _show_result(self, result: dict):
        self.status.set("Analysis complete")
        self.analyze_btn.config(state="normal")
        self.play_btn.config(state="normal")

        observation = result.get("observation") or {}
        candidates = result.get("candidates") or []

        word_recognition = result.get("wordRecognition") or {}
        word_text = str(word_recognition.get("text") or "").strip()
        word_valid = word_recognition.get("status") == "candidate_transcription" and bool(word_text)
        lines = [
            "POSSIBLE SPOKEN WORDS",
            word_text if word_valid else "Word recognition unavailable — review saved audio.",
            "Unverified AI suggestion; caregiver confirmation required.",
        ]
        if result.get("reanalysisIntegrity", {}).get("wavIntegrityPassed"):
            lines.extend(["", "WAV integrity check passed. Report saved under Analytics > Integrity Reports."])
        lines.extend(_phoneme_review_warning_lines(result))
        lines.extend(_recognition_diagnostic_lines(result))
        lines.extend(["", "OBSERVED SPEECH SOUNDS (PHONEMES — UNVERIFIED MODEL OUTPUT)"])
        if isinstance(observation, dict):
            phonemes = observation.get("observedPhonemes") or observation.get("phonemes") or observation.get("ipa")
            transcript = observation.get("transcript") or result.get("transcript")
            if transcript:
                if _phoneme_review_warning_lines(result):
                    lines.append("Screen preview: " + _raw_phoneme_preview(transcript))
                    lines.append("Full unchanged phoneme sequence remains under Evidence and Raw JSON.")
                else:
                    lines.append(str(transcript))
            if phonemes and not _phoneme_review_warning_lines(result):
                lines.append(f"Phoneme sequence: {phonemes}")
        lines.append("Phoneme observations are not English word transcripts.")

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

        number_review = result.get("numberReview") or {}
        if number_review:
            lines.append("\nWORD-BY-WORD REVIEW (unconfirmed suggestions)")
            lines.append("Time (s)       Heard sounds        Suggested number / status")
            merges = result.get("proposedSegmentJoins") or []
            affected = {int(i) for m in merges for i in m.get("segmentIndices", [])}
            for entry in number_review.get("segments", []):
                idx = entry.get("segmentIndex", -1)
                word = entry.get("suggestedWord") or "Unresolved"
                mark = " [CHECK BOUNDARY]" if idx in affected else " [REVIEW]"
                lines.append(f"{entry.get('startSeconds', 0):5.2f}-{entry.get('endSeconds', 0):5.2f}   "
                             f"/{entry.get('observedPhonemes', '')}/   {word}{mark}")
                matches = entry.get("acousticMatches") or []
                if matches:
                    first = matches[0]
                    lines.append(f"    Acoustic reference: {first.get('kind')} / {first.get('number')} "
                                 f"(distance {first.get('acousticDistance')}; NOT accuracy)")
            for merge in merges:
                options = merge.get("candidates") or []
                top = options[0] if options else {}
                suggestion = top.get("word") or top.get("candidate") or "unknown"
                lines.append(f"Possible join {merge.get('segmentIndices')}: "
                             f"/{merge.get('observedPhonemes', '')}/ -> {suggestion} (confirm by listening)")
            count = number_review.get("referenceCount", 0)
            lines.append(f"\nReference library: {count} WAV(s) "
                         f"({number_review.get('standardCount', 0)} standard, "
                         f"{number_review.get('studentCount', 0)} student)")
            if not count:
                lines.append("No reference WAVs found for this student. Open the main Parent PC "
                             "window > Reference Audio Library; add individual number WAVs, "
                             "then analyze again. Check the Speaker / Student ID.")
            elif number_review.get("status") == "reference_library_error":
                lines.append("Reference library error: " + str(number_review.get("detail", "unknown")))
            lines.append("All interpretations require human review. Nothing above is automatically learned.")

        quality = result.get("recordingQuality") or {}
        if isinstance(quality, dict) and quality:
            score = quality.get("score")
            label = quality.get("label", "")
            usable = quality.get("usable")
            if isinstance(score, (int, float)):
                lines.append(f"\nTechnical recording quality: {int(score * 100)}% ({label}); "
                             "NOT word accuracy or verified speech/ambient separation.")
            if quality.get("reviewRecommended"):
                warning = quality.get("reliabilityWarning") or (
                    "Review original audio before accepting any speech suggestions.")
                lines.append("CAREGIVER REVIEW RECOMMENDED: " + str(warning))
            issues = quality.get("issues") or []
            if issues:
                lines.append("Recording quality flags (review recommended): " +
                             ", ".join(str(x).replace("_", " ") for x in issues))
            noise = (quality.get("metrics") or {}).get("noiseAssessment")
            if noise == "possible_background_noise":
                lines.append("Background-noise screening: possible elevated noise floor "
                             "(heuristic estimate; not validated speech SNR).")
            elif isinstance(noise, str) and noise.startswith("not_measured_"):
                lines.append("Background-noise screening: not measured; insufficient "
                             "quiet/active evidence to estimate a noise floor.")
            if usable is False:
                lines.append("Quality screen marked this audio unreliable; any speech "
                             "suggestions must be treated as uncertain.")

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
                    lines.append(f"• Speech rate: {rate_band} ({sps:.2f} energy peaks/sec (not verified syllables))")
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
            elif phoneme_analysis.get("phonemeCount", 0):
                lines.append("\nPhoneme confidence: not measured for every sound; review required.")
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

        if word_valid:
            self.confirmed_word.set(word_text)
        elif isinstance(candidates, list) and candidates and isinstance(candidates[0], dict):
            self.confirmed_word.set(str(candidates[0].get("word") or candidates[0].get("candidate") or ""))

        if self.current_file:
            profile_meta = _load_metadata(self.current_file)
            lines.append("")
            lines.append("SPEAKER / COUNTING DIAGNOSTICS")
            lines.append(f"Speaker: {profile_meta.get('speakerId', 'unknown')} | Role: {profile_meta.get('speakerRole', 'unclassified')}")
            if profile_meta.get('countingDiagnostic'):
                lines.append("Expected sequence (caregiver context only): one two three four five six seven eight nine ten eleven twelve")
                lines.append("IMPORTANT: Expected words are not recognition results or verified accuracy.")
                lines.append("Review each clip and boundary; never train from an expected number alone.")
            if profile_meta.get('speakerRole') == 'Adult test / reference':
                lines.append("ADULT TEST: Keep out of child-specific learning; store as standard reference only after review.")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("1.0", "\n".join(lines))

        if self.current_file:
            meta = _load_metadata(self.current_file)
            self.approval_status.set(meta.get("reviewStatus", "Not reviewed").replace("_", " ").title())


    def open_segment_review(self):
        """Review word clips without altering original audio or observations."""
        if getattr(self, "_analysis_in_flight", False):
            messagebox.showinfo("Analysis in progress", "Please finish analysis before confirming any word clips.")
            return
        if self.recording:
            messagebox.showinfo("Finish recording", "Please tap Stop before reviewing recorded words.")
            return
        result = self.last_result or {}
        segments = (result.get("numberReview") or {}).get("segments") or []
        if not self.current_file or not self.current_file.exists() or not segments:
            messagebox.showinfo("Word review", "Analyze a recording with word clips first.")
            return
        wav_path = self.current_file
        meta = _load_metadata(wav_path)
        review_path = SEGMENT_REVIEWS_DIR / (wav_path.stem + "_segments.json")
        try:
            saved = json.loads(review_path.read_text(encoding="utf-8")) if review_path.exists() else {}
        except (OSError, ValueError):
            saved = {}
        previous = reusable_previous_reviews(
            saved, meta.get("observationId"), segments,
        )
        review_generation = self._analysis_generation
        review_observation_id = str(meta.get("observationId") or "")

        window = tk.Toplevel(self)
        window.title(f"Review individual words - {wav_path.name} - Hearlium")
        window.geometry("1020x625")
        window.minsize(760, 470)
        tk.Label(window, text=f"Listen and review each word — {wav_path.name}", font=("Segoe UI", 13, "bold")).pack(
            anchor="w", padx=14, pady=(12, 3))
        tk.Label(window, text=(
            "1. Play a clip.  2. Correct the word if needed.  "
            "3. Choose Confirm only when you are sure the clip contains one complete word.  "
            "Choose Unsure if the word or its start/end is unclear.  "
            "4. Save your reviews. You never have to guess."
        ), wraplength=970, justify="left").pack(anchor="w", padx=14, pady=(0, 5))
        tk.Label(window, text=(
            "Confirming saves a verified clip for possible future learning; "
            "saving reviews does NOT retrain the model."
        ), wraplength=970, justify="left", fg="#42526e").pack(anchor="w", padx=14, pady=(0, 8))

        holder = tk.Frame(window)
        holder.pack(fill="both", expand=True, padx=12)
        canvas = tk.Canvas(holder, highlightthickness=0)
        scrollbar = ttk.Scrollbar(holder, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        for col, heading in enumerate(("Clip / timing", "Word you heard", "Your decision", "Listen", "Correct")):
            tk.Label(inner, text=heading, font=("Segoe UI", 9, "bold"), anchor="w").grid(
                row=0, column=col, sticky="w", padx=5, pady=(3, 7))
        inner.columnconfigure(0, minsize=250)
        inner.columnconfigure(1, minsize=190)
        inner.columnconfigure(2, minsize=145)
        rows = []
        joins = result.get("proposedSegmentJoins") or []
        ambiguous = {int(i) for j in joins for i in j.get("segmentIndices", [])}

        def focus_word(row, *, select_text=False):
            # Navigate to the flagged clip even when it is off-screen.
            window.update_idletasks()
            row_height = max(1, inner.winfo_height() - canvas.winfo_height())
            canvas.yview_moveto(min(1.0, max(0.0, row["heading"].winfo_y() / row_height)))
            row["heading"].configure(bg="#fff0bd")
            row["entry"].focus_set()
            if select_text:
                row["entry"].selection_range(0, "end")
                row["entry"].icursor("end")

        for rownum, segment in enumerate(segments, 1):
            idx = int(segment.get("segmentIndex", rownum - 1))
            start, end = float(segment.get("startSeconds", 0)), float(segment.get("endSeconds", 0))
            original = str(segment.get("suggestedWord") or "")
            existing = previous.get(str(idx), {})
            word = tk.StringVar(value=existing.get("correctedWord", original))
            choice = tk.StringVar(value=display_decision(existing.get("status", "not_reviewed")))
            uncertain = idx in ambiguous or (end - start < .15)
            heading = tk.Label(inner, text=f"Word {rownum}  ({start:.2f}-{end:.2f}s)",
                               font=("Segoe UI", 10, "bold"), anchor="w")
            heading.grid(row=rownum * 2 - 1, column=0, sticky="w", padx=5, pady=(5, 0))
            note = "Start/end unclear - choose Unsure" if uncertain else f"Sounds: /{segment.get('observedPhonemes', '')}/"
            tk.Label(inner, text=note, fg="#8a5500" if uncertain else "#555555", anchor="w").grid(
                row=rownum * 2, column=0, sticky="w", padx=5, pady=(0, 6))
            entry = tk.Entry(inner, textvariable=word, width=23)
            entry.grid(row=rownum * 2 - 1, column=1, rowspan=2, sticky="w", padx=5)
            ttk.Combobox(inner, textvariable=choice, state="readonly", width=15,
                         values=tuple(DECISION_TO_STATUS)).grid(
                             row=rownum * 2 - 1, column=2, rowspan=2, sticky="w", padx=5)
            tk.Button(inner, text="Play clip", command=lambda a=start, b=end:
                      self._play_segment_clip(wav_path, a, b)).grid(
                          row=rownum * 2 - 1, column=3, rowspan=2, padx=4)
            row = {"idx": idx, "number": rownum, "start": start, "end": end,
                   "original": original, "word": word, "choice": choice,
                   "uncertain": uncertain, "segment": segment,
                   "heading": heading, "entry": entry}
            tk.Button(inner, text="Correct", command=lambda r=row: (
                r["choice"].set("Not reviewed"), focus_word(r, select_text=True))).grid(
                    row=rownum * 2 - 1, column=4, rowspan=2, padx=4)
            # An edited word is not automatically a verified word. Confirm explicitly again.
            def on_edit(*_args, r=row):
                if r["choice"].get() == "Confirm":
                    r["choice"].set("Not reviewed")
            word.trace_add("write", on_edit)
            rows.append(row)

        notice = tk.StringVar(value="Unsure and Reject can always be saved without approving a clip for learning.")
        tk.Label(window, textvariable=notice, wraplength=970, justify="left").pack(
            anchor="w", padx=14, pady=(8, 4))

        def ask_to_review(row, reason, label):
            """An actionable dialog: navigate to the problem or mark the word Unsure."""
            popup = tk.Toplevel(window)
            popup.title(f"Please check Word {row['number']}")
            popup.transient(window)
            popup.resizable(False, False)
            popup.grab_set()
            tk.Label(popup, text=f"Please check Word {row['number']}",
                     font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(14, 4))
            tk.Label(popup, text=caregiver_explanation(reason, row["number"], label).split("\n\n", 1)[-1],
                     wraplength=495, justify="left").pack(anchor="w", padx=16, pady=(0, 12))
            actions = tk.Frame(popup)
            actions.pack(padx=16, pady=(0, 14), anchor="e")
            def review():
                popup.destroy()
                focus_word(row, select_text=reason != "unclear_boundary")
            def mark_unsure():
                row["choice"].set("Unsure")
                notice.set(f"Word {row['number']} marked Unsure. Click Save reviews to keep all your decisions.")
                popup.destroy()
                focus_word(row)
            tk.Button(actions, text=f"Review Word {row['number']}", command=review).pack(side="left", padx=4)
            tk.Button(actions, text="Mark Unsure", command=mark_unsure).pack(side="left", padx=4)
            tk.Button(actions, text="Cancel", command=popup.destroy).pack(side="left", padx=4)
            popup.bind("<Escape>", lambda _e: popup.destroy())
            popup.wait_window()

        def save():
            # A dialog from an older analysis must not approve newly segmented audio.
            latest_observation_id = str(_load_metadata(wav_path).get("observationId") or "")
            if (self.recording or self.current_file != wav_path
                    or self._analysis_generation != review_generation
                    or latest_observation_id != review_observation_id):
                messagebox.showwarning("Recording changed",
                    "This recording or its analysis changed. Close this word-review window and reopen it to check the current clips.",
                    parent=window)
                return
            # Validate ALL choices before exporting ANY learning clips or changing the manifest.
            # A blocked confirmation must not cause partial commits of earlier rows.
            checked = []
            for row in rows:
                label = row["word"].get().strip().lower()
                status = DECISION_TO_STATUS[row["choice"].get()]
                if status == "confirmed":
                    reason = confirmation_issue(
                        label, boundary_uncertain=row["uncertain"],
                        adult_reference=meta.get("speakerRole") == "Adult test / reference")
                    if reason:
                        ask_to_review(row, reason, label)
                        return
                checked.append((row, label, status))

            data = {"schemaVersion": 1, "recording": str(wav_path),
                    "observationId": meta.get("observationId"),
                    "speakerId": meta.get("speakerId") or self.speaker_id.get(),
                    "speakerRole": meta.get("speakerRole", "unclassified"),
                    "savedAt": datetime.now().isoformat(timespec="seconds"), "reviews": {}}
            approved = 0
            for row, label, status in checked:
                idx, start, end = row["idx"], row["start"], row["end"]
                segment = row["segment"]
                item = {"segmentIndex": idx, "startSeconds": start, "endSeconds": end,
                        "observedPhonemes": segment.get("observedPhonemes", ""),
                        "suggestedWord": row["original"], "correctedWord": label, "status": status,
                        "boundaryFlagged": row["uncertain"], "approvedForLearning": status == "confirmed"}
                approved += int(status == "confirmed")
                data["reviews"][str(idx)] = item
            try:
                # Clip generation is private until all clips and the manifest are valid.
                # On failure, the previous manifest and previously approved clips remain.
                commit_review_manifest(wav_path, review_path, data, APPROVED_CLIPS_DIR)
            except Exception as error:
                messagebox.showerror("Could not save word reviews",
                                     f"Your previous reviews are unchanged.\n\n{error}", parent=window)
                notice.set("Save failed. Existing reviews were not replaced; check storage and retry.")
                return
            notice.set(f"Saved {len(rows)} word reviews; {approved} confirmed for future verified learning. No model update performed.")
            self.status.set("Individual caregiver reviews saved")
            messagebox.showinfo("Word reviews saved", (
                f"Saved {len(rows)} word decisions, including {approved} confirmed clips.\n"
                "No model training was triggered."), parent=window)

        tk.Button(window, text="Save reviews", command=save,
                  font=("Segoe UI", 10, "bold")).pack(pady=(4, 12))

    def _play_segment_clip(self, wav_path: Path, start: float, end: float):
        """Play only the selected word interval, without modifying the original WAV."""
        try:
            import numpy as np
            import soundfile as sf
            import sounddevice as sd
            audio, sr = sf.read(str(wav_path), dtype="float32", always_2d=False)
            if audio.ndim > 1:
                audio = audio.mean(axis=1)
            lo = max(0, int(start * sr))
            hi = min(len(audio), int(end * sr))
            if hi <= lo:
                raise ValueError("Segment contains no audio")
            sd.stop()
            sd.play(np.asarray(audio[lo:hi], dtype="float32"), sr, blocking=False)
        except Exception as exc:
            messagebox.showerror("Clip playback", str(exc))

    def _feedback_payload(self, approved: bool, correction_only: bool = False):
        if getattr(self, "_analysis_in_flight", False):
            raise ValueError("Please finish analysis before saving caregiver feedback.")
        wav_path = self.current_file
        if not wav_path:
            raise ValueError("No recording is loaded.")
        meta = _load_metadata(wav_path)
        # An observation ID in metadata alone MUST NOT authorize a new review.
        observation_id = require_verified_loaded_analysis(
            wav_path, meta, getattr(self, "last_result", None), ANALYSIS_RESULTS_DIR)
        if _has_unresolved_learning_feedback(meta):
            raise ValueError(
                "A previous learning approval may still be active or unresolved. "
                "Please check Phase 3 Learning History and the local feedback audit "
                "before submitting another approval. You can still choose Unsure or Reject.")

        word = self.confirmed_word.get().strip()
        if not word and approved:
            raise ValueError("Enter the confirmed or corrected word before approving it for learning.")

        return meta, {
            "observation_id": observation_id,
            "speaker_id": str(meta.get("speakerId") or self.speaker_id.get().strip() or "anonymous"),
            "recording_id": str(meta.get("recordingId") or wav_path.stem),
            "confirmed_word": "" if correction_only else word,
            "corrected_word": word if correction_only else "",
            "approved_for_learning": "true" if approved else "false",
        }

    def _record_local_decision(self, decision: str, changes: dict) -> None:
        """Apply a newer caregiver decision without awaiting a pending API reply."""
        wav_path = self.current_file
        if not wav_path:
            raise ValueError("Load a recording before reviewing it.")
        previous: dict = {}
        def update(meta):
            nonlocal previous
            prior_ref = _active_approval(meta)
            prior_feedback = meta.get("learningFeedback")
            if prior_ref and str(prior_ref.get("exampleId") or ""):
                previous = {
                    "feedback": {"approvedForLearning": True, "exampleId": prior_ref["exampleId"]},
                    "observationId": str(prior_ref.get("observationId") or meta.get("observationId") or ""),
                    "speakerId": str(prior_ref.get("speakerId") or meta.get("speakerId") or ""),
                }
            unidentified_prior_approval = bool(prior_ref and not prior_ref.get("exampleId"))
            pending = meta.get("feedbackPending")
            outstanding_approval = (dict(pending) if isinstance(pending, dict) and
                                    pending.get("reviewStatus") == "approved_for_learning" else None)
            # If the API response never comes back, the durable marker prevents
            # a newer rejection from silently hiding an uncertain old approval.
            outstanding_approval = outstanding_approval or meta.get("supersededFeedbackPending")
            prior_state = meta.get("learningRevocationStatus")
            unresolved_states = ("pending", "awaiting_api_resolution", "ACTION_REQUIRED")
            # Keep an existing unresolved rollback lock even if the caregiver
            # makes another local decision or requests a new analysis.
            request_revoke_id = meta.get("learningRevocationRequestId")
            if previous:
                if prior_state in unresolved_states:
                    # An existing rollback owns this approval. Do not issue a
                    # second revocation or replace its reconciliation token.
                    previous.clear()
                    revocation_id = meta.get("learningRevocationId")
                    next_state = prior_state
                else:
                    revocation_id = uuid.uuid4().hex
                    previous["revocationId"] = revocation_id
                    next_state = "pending"
                    request_revoke_id = None
            elif unidentified_prior_approval:
                # Reject/Unsure must remain possible, but an accepted approval
                # with no server example ID cannot be considered revoked.
                revocation_id = meta.get("learningRevocationId")
                next_state = "ACTION_REQUIRED"
            elif outstanding_approval:
                revocation_id = meta.get("learningRevocationId")
                next_state = prior_state if prior_state in unresolved_states else "awaiting_api_resolution"
                if prior_state not in unresolved_states:
                    request_revoke_id = outstanding_approval.get("requestId")
            else:
                revocation_id = meta.get("learningRevocationId")
                next_state = prior_state
            return {
                **changes,
                "reviewStatus": decision,
                "reviewedAt": datetime.now().isoformat(timespec="seconds"),
                "reviewRevision": review_revision(meta) + 1,
                "feedbackPending": None,
                "supersededFeedbackPending": outstanding_approval,
                "learningFeedback": None,
                "learningUnresolvedApprovedFeedback": (prior_feedback if unidentified_prior_approval
                    else meta.get("learningUnresolvedApprovedFeedback")),
                "learningApprovalReferences": _approval_refs(meta),
                "learningRevocationExampleId": (previous.get("feedback") or {}).get("exampleId") if previous
                    else meta.get("learningRevocationExampleId"),
                "learningRevocationId": revocation_id,
                "learningRevocationRequestId": request_revoke_id,
                "learningRevocationStatus": next_state,
            }
        new_meta = _update_metadata(wav_path, update)
        if previous:
            self._revoke_prior_approval_after_decision(
                wav_path, previous, review_revision(new_meta))

    def _revoke_prior_approval_after_decision(self, wav_path: Path, prior: dict, decision_revision: int):
        """A new rejection/unsure also withdraws an already committed approval."""
        api_url = self.api_base()
        def worker():
            try:
                outcome = _audit_and_revoke_superseded_approval(
                    wav_path, prior["observationId"], prior["observationId"],
                    prior["feedback"], api_url=api_url, speaker_id=prior["speakerId"],
                    expected_revision=decision_revision - 1,
                    current_revision=decision_revision)
            except Exception as exc:
                # Even a logging/disk failure must not silently claim rollback.
                outcome = {"revoked": False, "auditPath": "Audit write failed",
                           "error": str(exc)}
            def commit(meta):
                # Revisions can advance while the rollback request is running.
                # Identify the *rollback*, not the last caregiver decision.
                if meta.get("learningRevocationId") != prior.get("revocationId"):
                    # Preserve every failure even if the request identity changed.
                    # Never mislabel a failed server rollback as resolved.
                    return ({"learningRevocationStatus": "ACTION_REQUIRED"}
                            if not outcome["revoked"] else {})
                return {"learningRevocationStatus": "revoked" if outcome["revoked"] else "ACTION_REQUIRED",
                        "learningApprovalReferences": _mark_approval_revoked(
                            meta, str(prior["feedback"].get("exampleId") or "")) if outcome["revoked"]
                            else _approval_refs(meta),
                        "learningRevocationExampleId": None if outcome["revoked"] else prior["feedback"].get("exampleId"),
                        "learningRevocationId": None if outcome["revoked"] else prior["revocationId"]}
            _update_metadata(wav_path, commit)
            self.after(0, self._finish_prior_approval_revocation, wav_path, outcome)
        threading.Thread(target=worker, daemon=True).start()

    def _finish_prior_approval_revocation(self, wav_path: Path, outcome: dict):
        if not outcome["revoked"]:
            messagebox.showwarning(
                "Learning rollback requires attention",
                "The caregiver decision was saved, but an earlier approval could not "
                "be revoked on the local learning server. Open Phase 3 Learning History "
                "to revoke the old example before using personalized learning.\n\n"
                f"Recording: {wav_path.name}\nAudit: {outcome['auditPath']}\n"
                f"Reason: {outcome.get('error', 'unknown')}")
        else:
            self.status.set("Earlier learning approval revoked after newer caregiver decision")

    def simple_confirm_and_save(self):
        text = self.confirmed_word.get().strip()
        if not text:
            messagebox.showinfo("Caregiver Review", "Enter what was said, then tap Confirm & Save.")
            return
        # Save complete utterances as caregiver feedback, NOT as a single-word
        # pronunciation example. Word-level learning remains in Advanced Review.
        self._submit_feedback(review_status="confirmed_sentence", approved=False, correction_only=True)

    def simple_unsure(self):
        if getattr(self, "recording", False):
            messagebox.showinfo("Finish recording", "Please finish recording before changing a caregiver decision.")
            return
        if getattr(self, "_analysis_in_flight", False):
            messagebox.showinfo("Analysis in progress", "Please finish analysis before changing a caregiver decision.")
            return
        if not self.current_file:
            messagebox.showinfo("Caregiver Review", "Load or analyze a recording first.")
            return
        self._record_local_decision("unsure", {})
        self.approval_status.set("Unsure — no learning")
        self.refresh_history()

    def approve_for_learning(self):
        if len(((self.last_result or {}).get("numberReview") or {}).get("segments") or []) > 1:
            messagebox.showwarning("Individual review required", "This recording contains multiple speech segments. Use 'Review Individual Words' instead. Whole-recording learning is blocked.")
            return
        self._submit_feedback(review_status="approved_for_learning", approved=True, correction_only=False)

    def save_correction_only(self):
        self._submit_feedback(review_status="corrected_not_approved", approved=False, correction_only=True)

    def reject_interpretation(self):
        if getattr(self, "recording", False):
            messagebox.showinfo("Finish recording", "Please finish recording before changing a caregiver decision.")
            return
        if getattr(self, "_analysis_in_flight", False):
            messagebox.showinfo("Analysis in progress", "Please finish analysis before changing a caregiver decision.")
            return
        if not self.current_file:
            messagebox.showinfo("Review", "Load or analyze a recording first.")
            return
        entered_notes = self.notes.get().strip()
        self._record_local_decision("rejected", {
            "confirmedWord": self.confirmed_word.get().strip(),
            "notes": entered_notes or _load_metadata(self.current_file).get("notes", ""),
        })
        self.approval_status.set("Rejected")
        self.refresh_history()
        messagebox.showinfo(
            "Interpretation rejected",
            "The interpretation is marked rejected locally. If an earlier approval was "
            "accepted by the learning server, Hearlium will attempt to revoke it and "
            "warn you if manual rollback is required."
        )

    def _submit_feedback(self, review_status: str, approved: bool, correction_only: bool):
        if self._feedback_in_flight:
            messagebox.showinfo("Caregiver Review", "A feedback save is already in progress. Please check its result before trying again.")
            return
        try:
            _meta, payload = self._feedback_payload(approved, correction_only)
        except ValueError as exc:
            messagebox.showinfo("Caregiver Review", str(exc))
            return

        # Snapshot every value before the network request. No Tk variables or
        # mutable current_file values are accessed from the worker thread.
        feedback_file = self.current_file
        feedback_observation_id = str(payload["observation_id"]).strip()
        feedback_word = self.confirmed_word.get().strip()
        feedback_notes = self.notes.get().strip()
        api_url = self.api_base()
        request_id = uuid.uuid4().hex
        payload["client_request_id"] = request_id
        # Even a correction-only request must revoke an earlier approved
        # example *before* overwriting its only local server reference.
        prior_approval = None
        prior_revocation_id = None
        try:
            def reserve(meta):
                # Close the time-of-check/time-of-use window between validating
                # the UI result and reserving this decision's revision.
                current_id = require_verified_loaded_analysis(
                    feedback_file, meta, getattr(self, "last_result", None), ANALYSIS_RESULTS_DIR)
                if current_id != feedback_observation_id:
                    raise ValueError("Analysis changed while preparing feedback. Reload and review before approval.")
                if _has_unresolved_learning_feedback(meta):
                    raise ValueError("Previous feedback outcome is unresolved. Verify Learning History before approving again.")
                nonlocal prior_approval, prior_revocation_id
                prior_approval = _active_approval(meta)
                if prior_approval:
                    prior_revocation_id = uuid.uuid4().hex
                updates = {
                    "reviewRevision": review_revision(meta) + 1,
                    "feedbackPending": {"observationId": feedback_observation_id,
                        "reviewStatus": review_status, "requestId": request_id,
                        "createdAt": datetime.now().isoformat(timespec="seconds")},
                }
                if prior_approval:
                    updates.update({
                        "learningApprovalReferences": _approval_refs(meta),
                        "learningRevocationStatus": "pending",
                        "learningRevocationId": prior_revocation_id,
                        "learningRevocationExampleId": prior_approval.get("exampleId"),
                    })
                return updates
            pending_meta = _update_metadata(feedback_file, reserve)
        except ValueError as exc:
            messagebox.showinfo("Caregiver Review", str(exc))
            return
        feedback_revision = review_revision(pending_meta)
        self._feedback_in_flight = True
        self.status.set("Saving caregiver feedback…")

        def worker():
            response_accepted = False
            try:
                if prior_approval:
                    # The old example must be revoked before any replacement
                    # feedback is sent, including a new approval for the word.
                    try:
                        if not str(prior_approval.get("exampleId") or ""):
                            raise ValueError("Old learning approval has no example ID; manual reconciliation required")
                        _revoke_remote_approval(api_url,
                            str(prior_approval.get("speakerId") or payload["speaker_id"]),
                            {"approvedForLearning": True, "exampleId": prior_approval["exampleId"]},
                            reason="caregiver_replaced_approved_word")
                    except Exception as rollback_error:
                        def blocked(meta):
                            changes = {}
                            if _matching_feedback_request(meta.get("feedbackPending"), request_id,
                                                          feedback_observation_id):
                                changes["feedbackPending"] = None
                            # A later local Reject/Unsure cannot hide a failed
                            # rollback of the original approved example.
                            changes["learningRevocationStatus"] = "ACTION_REQUIRED"
                            changes["learningRevocationExampleId"] = prior_approval.get("exampleId")
                            return changes
                        _update_metadata(feedback_file, blocked)
                        self.after(0, self._finish_feedback_save, feedback_file,
                            review_status, approved,
                            "Earlier approved learning example was NOT revoked; correction was NOT submitted. "
                            "Open Learning History and revoke the original example. " + str(rollback_error),
                            feedback_revision)
                        return
                    def completed(meta):
                        changed = {"learningApprovalReferences": _mark_approval_revoked(
                                        meta, str(prior_approval["exampleId"]))}
                        if meta.get("learningRevocationId") == prior_revocation_id:
                            changed.update({"learningRevocationStatus": "revoked",
                                            "learningRevocationId": None,
                                            "learningRevocationExampleId": None})
                            if (review_revision(meta) == feedback_revision and
                                meta.get("reviewStatus") == "approved_for_learning"):
                                # The old example has actually been revoked;
                                # if the replacement HTTP request fails the
                                # recording must NOT still appear approved.
                                changed["reviewStatus"] = "not_reviewed"
                        return changed
                    _update_metadata(feedback_file, completed)
                    # If the caregiver changed their decision while the old
                    # example was being revoked, do not post stale feedback.
                    latest = _load_metadata(feedback_file)
                    if (review_revision(latest) != feedback_revision or
                        str(latest.get("observationId") or "") != feedback_observation_id or
                        not _matching_feedback_request(latest.get("feedbackPending"), request_id,
                                                       feedback_observation_id)):
                        _resolve_definite_feedback_rejection(feedback_file, request_id,
                                                              feedback_observation_id)
                        self.after(0, self._finish_feedback_superseded, feedback_file,
                                   {"revoked": True, "notNeeded": False})
                        return
                response = requests.post(
                    f"{api_url}/v1/learning/feedback", data=payload, timeout=30
                )
                response.raise_for_status()
                result = response.json()
                response_accepted = True
                write_event("caregiver_feedback_accepted", httpStatus=response.status_code)
                if not feedback_file or not feedback_file.exists():
                    raise FileNotFoundError("Feedback was accepted by the API, but the original recording is no longer available; local review metadata was not saved.")
                # Both the *observation* and *decision revision* are checked
                # INSIDE the metadata lock. A subsequent Reject/Unsure always wins.
                def merge_only_if_current(meta):
                    current_observation = str(meta.get("observationId") or "").strip()
                    current_revision = review_revision(meta)
                    if (current_observation != feedback_observation_id or
                            current_revision != feedback_revision):
                        raise ReviewDecisionSuperseded(current_observation, current_revision)
                    return {
                        "reviewStatus": review_status,
                        "reviewedAt": datetime.now().isoformat(timespec="seconds"),
                        "confirmedWord": feedback_word,
                        "notes": feedback_notes or meta.get("notes", ""),
                        "learningFeedback": result,
                        "learningApprovalReferences": _remember_new_approval(
                            meta, result, payload["speaker_id"], feedback_observation_id,
                            request_id),
                        "feedbackPending": None,
                        "learningRevocationStatus": ("revoked" if prior_approval else None),
                        "learningRevocationRequestId": None,
                    }
                try:
                    _update_metadata(feedback_file, merge_only_if_current)
                except ReviewDecisionSuperseded as changed:
                    outcome = _audit_and_revoke_superseded_approval(
                        feedback_file, feedback_observation_id, changed.observation, result,
                        api_url=api_url, speaker_id=payload["speaker_id"],
                        expected_revision=feedback_revision, current_revision=changed.revision)
                    _resolve_superseded_feedback(
                        feedback_file, request_id, feedback_observation_id,
                        approved=approved, revoked=outcome["revoked"])
                    write_event("caregiver_feedback_superseded_decision",
                                revocationSucceeded=outcome["revoked"])
                    self.after(0, self._finish_feedback_superseded, feedback_file, outcome)
                    return
                self.after(0, self._finish_feedback_save, feedback_file, review_status,
                           approved, None, feedback_revision)
            except Exception as exc:
                response = getattr(exc, "response", None)
                write_event("caregiver_feedback_request_failed",
                            errorType=type(exc).__name__,
                            httpStatus=getattr(response, "status_code", None),
                            winerror=getattr(exc, "winerror", None))
                error_text = str(exc)
                # Do not silently retry an uncertain network result: a timeout
                # could occur AFTER the API already accepted an approval.
                if response is not None and getattr(response, "status_code", 500) < 500 and not response_accepted:
                    # Definite HTTP 4xx response means this request was not
                    # accepted. Reconcile by request ID, not decision revision:
                    # Unsure/Reject may already have superseded it.
                    _resolve_definite_feedback_rejection(
                        feedback_file, request_id, feedback_observation_id)
                elif not approved:
                    # A non-learning correction cannot create a learning example,
                    # even if its HTTP response was lost. Do not strand an
                    # unresolved-*approval* marker or block correction retries.
                    def clear_correction(meta):
                        pending = meta.get("feedbackPending")
                        return {"feedbackPending": None} if (
                            isinstance(pending, dict) and
                            str(pending.get("requestId") or "") == request_id) else {}
                    _update_metadata(feedback_file, clear_correction)
                elif approved and not response_accepted:
                    # A timeout or lost response is AMBIGUOUS: the API may have
                    # committed the approval. Persist this for manual recovery.
                    def mark_ambiguous(meta):
                        if review_revision(meta) == feedback_revision:
                            return {"learningRevocationStatus": "ACTION_REQUIRED",
                                    "learningRevocationRequestId": request_id}
                        if _matching_feedback_request(meta.get("supersededFeedbackPending"),
                                                      request_id, feedback_observation_id):
                            return {"learningRevocationStatus": "ACTION_REQUIRED",
                                    "learningRevocationRequestId": request_id}
                        return {}
                    _update_metadata(feedback_file, mark_ambiguous)
                    audit = _append_feedback_observation_audit(
                        feedback_file, feedback_observation_id,
                        str(_load_metadata(feedback_file).get("observationId") or ""),
                        {"requestError": error_text, "approvedForLearning": approved})
                    _write_feedback_audit_update(audit, {
                        "reason": "Approval response outcome unknown; check server learning history",
                        "revocationStatus": "ACTION_REQUIRED",
                    })
                if approved and response_accepted:
                    # A received approval with a later audit/rollback error is
                    # not safe to treat as completed. Keep it blocked.
                    def mark_failure(meta):
                        # A subsequent observation/revision cannot erase an
                        # already accepted approval whose rollback was not verified.
                        return {"learningRevocationStatus": "ACTION_REQUIRED",
                                "learningRevocationRequestId": request_id}
                    _update_metadata(feedback_file, mark_failure)
                self.after(0, self._finish_feedback_save, feedback_file, review_status,
                           approved, error_text, feedback_revision)

        threading.Thread(target=worker, daemon=True).start()

    def _finish_feedback_superseded(self, feedback_file: Path, outcome: dict | None = None):
        self._feedback_in_flight = False
        self.refresh_history()
        if outcome is not None and not outcome.get("revoked", False):
            self.status.set("Learning rollback requires attention — newer decision preserved")
            messagebox.showwarning("Learning rollback requires attention", (
                "An earlier approval reached the local learning server after you changed "
                "your decision. Your newer decision was preserved, but automatic revocation "
                "FAILED. Open Phase 3 Learning History and revoke the old example. "
                "Do not use personalized learning until this is resolved.\n\n"
                f"Recording: {feedback_file.name}\n"
                f"Audit: {outcome.get('auditPath')}\nReason: {outcome.get('error')}"))
        else:
            self.status.set("Earlier API feedback superseded; newer caregiver decision preserved")
            messagebox.showwarning("Earlier feedback superseded", (
                "The API replied for an earlier analysis or caregiver decision. "
                "The newer review remains unchanged. Any older learning approval "
                "was revoked or did not require revocation.\n\n"
                f"Recording: {feedback_file.name}"))

    def _finish_feedback_save(self, feedback_file: Path, review_status: str, approved: bool,
                              error_text: str | None, feedback_revision: int | None = None):
        self._feedback_in_flight = False
        if error_text:
            if approved:
                explanation = (". If the API connection failed, verify Phase 3 Learning History "
                               "before retrying to avoid a duplicate approval.")
            else:
                if "NOT revoked" in error_text:
                    explanation = (". The earlier approved example may still influence learning; "
                                   "do not retry until manual rollback is confirmed.")
                else:
                    explanation = (". No learning approval was requested. Check caregiver "
                                   "review history before retrying to avoid duplicate corrections.")
            self._show_error("Feedback may not have been saved: " + error_text + explanation)
            return
        # Decision may have changed AFTER the worker committed but BEFORE Tk
        # delivered this callback. Never change GUI status back to Approved.
        meta = _load_metadata(feedback_file)
        if feedback_revision is not None and (review_revision(meta) != feedback_revision or
                                               meta.get("reviewStatus") != review_status):
            self.refresh_history()
            if self.current_file == feedback_file:
                self.approval_status.set(str(meta.get("reviewStatus") or "not_reviewed").replace("_", " ").title())
            self.status.set("Earlier feedback superseded by newer caregiver decision")
            return
        self.refresh_history()
        if self.current_file == feedback_file:
            self.status.set("Caregiver feedback saved")
            self.approval_status.set(review_status.replace("_", " ").title())
        else:
            self.status.set(f"Feedback saved for {feedback_file.name}; current recording unchanged")
        messagebox.showinfo("Caregiver Review", (
            "Approved for learning." if approved else "Correction saved without approving it for learning."
        ) + f"\n\nRecording: {feedback_file.name}")

    def _history_recognized_words(self, wav_path: Path, meta: dict) -> str:
        """Show saved *unverified* words for Android and Parent PC recordings."""
        if not meta.get("observationId"):
            return ""
        export_name = str(meta.get("analysisExport") or _safe_analysis_filename(wav_path).name)
        export = ANALYSIS_RESULTS_DIR / export_name
        if export.resolve().parent != ANALYSIS_RESULTS_DIR.resolve():
            return ""
        try:
            meta_stat = _metadata_path(wav_path).stat()
            meta_sig = (meta_stat.st_mtime_ns, meta_stat.st_size)
        except OSError:
            meta_sig = (0, 0)
        try:
            export_stat = export.stat()
            export_sig = (export_stat.st_mtime_ns, export_stat.st_size)
        except OSError:
            export_sig = (0, 0)
        signature = (meta_sig, export_sig, str(meta.get("observationId")))
        cache = getattr(self, "_history_android_words_cache", None)
        if cache is None:
            cache = {}
            self._history_android_words_cache = cache
        key = str(wav_path)
        cached = cache.get(key)
        if cached and cached[0] == signature:
            return cached[1]
        suggestion = ""
        try:
            result, _ = load_verified_saved_analysis(wav_path, meta, ANALYSIS_RESULTS_DIR)
            if result:
                recog = result.get("wordRecognition") or {}
                if isinstance(recog, dict):
                    suggestion = str(recog.get("text") or "").strip()
                if not suggestion:
                    candidates = result.get("candidates") or []
                    if candidates and isinstance(candidates[0], dict):
                        suggestion = str(candidates[0].get("word") or candidates[0].get("candidate") or "").strip()
        except (SavedAnalysisMismatch, OSError, ValueError):
            pass
        cache[key] = (signature, suggestion)
        return suggestion

    def _history_suggested_title(self, wav_path: Path, meta: dict) -> str:
        """Read *verified* existing analysis only; never run ASR for a title."""
        export_name = str(meta.get("analysisExport") or _safe_analysis_filename(wav_path).name)
        export = ANALYSIS_RESULTS_DIR / export_name
        export_signature = (0, 0)
        if export.resolve().parent == ANALYSIS_RESULTS_DIR.resolve():
            try:
                stat = export.stat()
                export_signature = (stat.st_mtime_ns, stat.st_size)
            except OSError:
                pass
        try:
            meta_stat = _metadata_path(wav_path).stat()
            signature = (meta_stat.st_mtime_ns, meta_stat.st_size, export_signature)
        except OSError:
            signature = (0, 0, export_signature)
        cache = getattr(self, "_history_title_suggestions_cache", {})
        cached = cache.get(str(wav_path))
        if cached and cached[0] == signature:
            return cached[1]
        verified_result = None
        try:
            verified_result, _ = load_verified_saved_analysis(wav_path, meta, ANALYSIS_RESULTS_DIR)
        except (SavedAnalysisMismatch, OSError, ValueError):
            pass
        title = suggested_title(wav_path, meta, verified_result)
        cache[str(wav_path)] = (signature, title)
        self._history_title_suggestions_cache = cache
        return title

    def _clear_selected_history_label_fields(self):
        self.history_custom_title.set("")
        self.history_custom_tags.set("")
        self.history_custom_notes.set("")
        self.history_suggested_title.set("Select a recording to see its suggested title.")

    def _selected_history_title_row(self, wav_path: Path):
        return next((row for row in self._history_cached_rows if row["path"] == wav_path), None)

    def save_selected_recording_label(self):
        if not self._ensure_not_recording():
            return
        wav_path = self._selected_history_path()
        if wav_path is None:
            return
        try:
            save_label(RECORDING_TITLES_PATH, RECORDING_TITLES_AUDIT_PATH,
                       RECORDINGS_DIR, wav_path, _load_metadata(wav_path),
                       self.history_custom_title.get(), self.history_custom_tags.get(),
                       self.history_custom_notes.get())
        except (OSError, ValueError) as exc:
            messagebox.showerror("Recording label", f"Cannot save this recording label: {exc}")
            return
        self.refresh_history()
        self.status.set("Recording label saved separately from original audio and analysis")

    def use_suggested_recording_title(self):
        if not self._ensure_not_recording():
            return
        wav_path = self._selected_history_path()
        if wav_path is None:
            return
        try:
            # Empty title restores the suggestion, preserving custom tags/notes.
            save_label(RECORDING_TITLES_PATH, RECORDING_TITLES_AUDIT_PATH,
                       RECORDINGS_DIR, wav_path, _load_metadata(wav_path), "",
                       self.history_custom_tags.get(), self.history_custom_notes.get())
        except (OSError, ValueError) as exc:
            messagebox.showerror("Recording label", f"Cannot restore suggested title: {exc}")
            return
        self.refresh_history()

    def save_suggested_titles_for_existing(self):
        if not self._ensure_not_recording():
            return
        if not messagebox.askyesno(
                "Save Suggested Titles", "Save suggested titles for the existing recordings?\n\n"
                "These labels are based only on existing metadata and verified saved analysis. "
                "Unverified AI words remain labeled as suggestions. "
                "Your custom titles, original WAVs, evidence and approved learning stay unchanged."):
            return
        rows = [(row["path"], _load_metadata(row["path"]), row["suggestedTitle"])
                for row in self._history_cached_rows]
        try:
            count = backfill_suggested_labels(
                RECORDING_TITLES_PATH, RECORDING_TITLES_AUDIT_PATH, RECORDINGS_DIR, rows)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Save Suggested Titles", f"Could not save suggested titles: {exc}")
            return
        self.refresh_history()
        messagebox.showinfo("Save Suggested Titles", f"Saved {count} suggested title(s). "
                            "Existing custom titles were preserved.")

    def refresh_history(self):
        if not hasattr(self, "history"):
            return
        profiles = load_profiles(STUDENT_PROFILES_PATH)
        try:
            label_index = load_labels(RECORDING_TITLES_PATH)
        except (OSError, ValueError) as exc:
            # A damaged index must never be overwritten by an empty replacement.
            self.history_count.set("Recording labels unavailable — check index")
            messagebox.showerror("Recording labels", str(exc))
            return
        self._history_labels = label_index
        rows = []
        for wav_path in RECORDINGS_DIR.glob("*.wav"):
            try:
                modified = wav_path.stat().st_mtime
            except OSError:
                continue
            meta = _load_metadata(wav_path)
            created = str(meta.get("createdAt") or datetime.fromtimestamp(modified).isoformat(timespec="seconds"))
            speaker = str(meta.get("speakerId") or "").strip()
            try:
                saved = label_for_recording(RECORDINGS_DIR, wav_path, meta, label_index)
            except (OSError, ValueError):
                saved = {}
            suggestion = self._history_suggested_title(wav_path, meta)
            custom = str(saved.get("customTitle") or "")
            rows.append({
                'path': wav_path, 'filename': wav_path.name, 'mtime': modified,
                'created': created, 'speakerId': speaker,
                'displayName': student_display_name(speaker, meta, profiles),
                'status': str(meta.get("reviewStatus", "not_reviewed")).replace("_", " "),
                'word': str(meta.get("confirmedWord") or meta.get("bestCandidate") or
                            self._history_recognized_words(wav_path, meta)),
                'title': custom or suggestion, 'suggestedTitle': suggestion,
                'customTitle': custom, 'tags': list(saved.get("tags") or []),
                'labelNotes': str(saved.get("notes") or ""),
            })
        self._history_cached_rows = rows
        ids = {row['speakerId'] for row in rows if not is_unassigned(row['speakerId'])}
        self._history_filter_lookup = {"All students": "ALL", "Unassigned": "__UNASSIGNED__"}
        for sid in sorted(ids, key=lambda key: (next(row['displayName'].casefold() for row in rows
                                                    if row['speakerId'] == key), key.casefold())):
            names = {row['displayName'] for row in rows if row['speakerId'] == sid}
            name = next(iter(names)) if len(names) == 1 else 'Shared ID (multiple recording labels)'
            label = f"{name}  [{sid}]"
            self._history_filter_lookup[label] = sid
        selected = self.history_student_filter.get()
        self.history_student_combo.configure(values=tuple(self._history_filter_lookup))
        if selected not in self._history_filter_lookup:
            self.history_student_filter.set("All students")
        self._apply_history_filters()

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
        row = self._selected_history_title_row(wav_path)
        if row is not None:
            self.history_custom_title.set(row.get("customTitle") or "")
            self.history_custom_tags.set(", ".join(row.get("tags") or []))
            self.history_custom_notes.set(row.get("labelNotes") or "")
            self.history_suggested_title.set(
                "Suggested: " + str(row.get("suggestedTitle") or "") +
                " | AI-derived words are unverified; labels do not approve learning.")
        details = {
            "file": wav_path.name,
            "recordingTitle": row.get("title") if row is not None else "",
            "customTags": row.get("tags") if row is not None else [],
            "customLabelNotes": row.get("labelNotes") if row is not None else "",
            "speakerId": meta.get("speakerId"),
            "studentName": student_display_name(meta.get("speakerId"), meta, load_profiles(STUDENT_PROFILES_PATH)),
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

    def _clear_loaded_analysis(self):
        """Invalidate stale analysis before showing audio from another recording."""
        lock = getattr(self, "_analysis_state_lock", None)
        if lock is None:  # Allow lightweight test harnesses without a GUI constructor.
            self._analysis_generation += 1
        else:
            with lock:
                self._analysis_generation += 1
        self._analysis_in_flight = False
        self.last_result = None
        self.last_analysis_export = None
        self.confirmed_word.set("")
        self.result_box.delete("1.0", "end")
        self.refresh_dashboard()
        self.refresh_evidence()
        self.refresh_raw_json()
        self.rebuild_analytics()

    def reanalyze_selected(self):
        if getattr(self, "recording", False):
            messagebox.showinfo("Finish recording", "Please tap Stop before changing recordings.")
            return
        if getattr(self, "_feedback_in_flight", False):
            messagebox.showinfo("Caregiver feedback pending", (
                "Finish the active caregiver feedback or rollback request before reanalysis."))
            return
        wav_path = self._selected_history_path()
        if not wav_path:
            return
        self._clear_loaded_analysis()
        self.current_file = wav_path
        meta = _load_metadata(wav_path)
        self.speaker_id.set(meta.get("speakerId", "student-1"))
        self.context.set(meta.get("context", ""))
        self.notes.set(meta.get("notes", ""))
        if getattr(self, "background_audio", None) is not None:
            self.background_audio.set(_background_audio_label(meta.get("backgroundAudioLabel")))
        self.file_text.set(str(wav_path))
        self._analysis_in_flight = True
        self.analyze_btn.config(state="disabled")
        self.approval_status.set("Analysis in progress — review unavailable")
        self.status.set("Reanalyzing…")
        threading.Thread(target=self._analyze_worker, args=(wav_path, self._analysis_generation, True), daemon=True).start()

    def load_selected_into_review(self):
        if getattr(self, "recording", False):
            messagebox.showinfo("Finish recording", "Please tap Stop before changing recordings.")
            return
        wav_path = self._selected_history_path()
        if not wav_path:
            return
        meta = _load_metadata(wav_path)
        self._clear_loaded_analysis()
        self.current_file = wav_path
        self.speaker_id.set(meta.get("speakerId", "student-1"))
        self.context.set(meta.get("context", ""))
        self.notes.set(meta.get("notes", ""))
        if getattr(self, "background_audio", None) is not None:
            self.background_audio.set(_background_audio_label(meta.get("backgroundAudioLabel")))
        self.confirmed_word.set(meta.get("confirmedWord") or meta.get("bestCandidate") or "")
        self.file_text.set(str(wav_path))
        self.approval_status.set(meta.get("reviewStatus", "not_reviewed").replace("_", " ").title())
        try:
            result, saved_export = load_verified_saved_analysis(wav_path, meta, ANALYSIS_RESULTS_DIR)
        except SavedAnalysisMismatch as exc:
            result, saved_export = None, None
            review_notice = f"Saved analysis cannot be verified for this recording: {exc}\nReanalyze before review."
        else:
            review_notice = "No saved analysis result. Click Analyze Recording."
        if isinstance(result, dict):
            self.last_result = result
            self.last_analysis_export = saved_export
            self._show_result(result)
            self.refresh_dashboard()
            self.refresh_evidence()
            self.refresh_raw_json()
            self.rebuild_analytics()
        else:
            self.confirmed_word.set("")
            self.result_box.delete("1.0", "end")
            self.result_box.insert("1.0", review_notice)
        if _has_unresolved_learning_feedback(meta):
            self.approval_status.set("Learning approval requires reconciliation")
            self.status.set("Check Phase 3 Learning History and local feedback audit before new approvals")
        self.analyze_btn.config(state="normal")
        self.play_btn.config(state="normal")

    def delete_selected_history(self):
        if getattr(self, "recording", False):
            messagebox.showinfo("Finish recording", "Please tap Stop before changing recordings.")
            return
        wav_path = self._selected_history_path()
        if not wav_path:
            return
        if not messagebox.askyesno("Delete Recording", f"Delete {wav_path.name} and its local review metadata?"):
            return
        try:
            if self.current_file == wav_path:
                self._clear_loaded_analysis()
                self.current_file = None
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
    app = DirectRecorder(initial_tab="history" if "--history" in sys.argv[1:] else "record")
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
