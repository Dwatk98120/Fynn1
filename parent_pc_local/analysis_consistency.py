"""Evidence-safe helpers for loading saved Android/Parent PC speech analysis.

The recording WAV is never edited. An analysis must prove both its recording
identity and observation identity before it is displayed as reviewable evidence.
"""
from __future__ import annotations

import json
from pathlib import Path


class SavedAnalysisMismatch(ValueError):
    """Saved analysis belongs to another recording/observation or is malformed."""


class ObservationChanged(RuntimeError):
    """Feedback for a prior observation must not update the current review."""


def observation_id(result: dict) -> str:
    observation = result.get("observation") if isinstance(result, dict) else None
    return str((observation or {}).get("observationId") or "").strip() if isinstance(observation, dict) else ""


def verify_analysis_identity(wav_path: Path, metadata: dict, result: dict) -> None:
    if not isinstance(result, dict):
        raise SavedAnalysisMismatch("Saved analysis is not a valid result.")
    expected_obs = str(metadata.get("observationId") or "").strip()
    result_obs = observation_id(result)
    if not expected_obs or not result_obs or expected_obs != result_obs:
        raise SavedAnalysisMismatch("Saved analysis does not match this recording's current observation.")
    expected_recording_id = str(metadata.get("recordingId") or "").strip()
    actual_recording_id = str(result.get("recordingId") or "").strip()
    if expected_recording_id and actual_recording_id and expected_recording_id != actual_recording_id:
        raise SavedAnalysisMismatch("Saved analysis refers to a different recording ID.")
    source = result.get("_parent_pc") or {}
    if isinstance(source, dict) and source.get("file"):
        expected_file = str(wav_path.resolve()).casefold()
        recorded_file = str(Path(str(source["file"])).resolve()).casefold()
        if recorded_file != expected_file:
            raise SavedAnalysisMismatch("Saved analysis refers to another audio file.")


def _trusted_export_path(wav_path: Path, metadata: dict, analysis_dir: Path) -> Path:
    """Versioned exports must remain in the local analysis directory."""
    base = analysis_dir.resolve()
    version_name = metadata.get("analysisExport")
    if version_name:
        path = base / str(version_name)
        if path.resolve().parent != base:
            raise SavedAnalysisMismatch("Saved analysis export has an invalid location.")
        if not path.name.startswith(f"{wav_path.stem}_analysis_") or not path.name.endswith(".json"):
            raise SavedAnalysisMismatch("Saved analysis export has an unexpected recording name.")
        return path
    return base / f"{wav_path.stem}_analysis.json"


def load_verified_saved_analysis(wav_path: Path, metadata: dict, analysis_dir: Path):
    """Return (analysis, export_path), loading Android's separate JSON when needed.

    Inline Parent PC analysis takes priority, but must also pass ID validation.
    Never substitute a stale on-disk export for an inline result that fails it.
    """
    inline = metadata.get("analysisResult")
    if inline is not None:
        verify_analysis_identity(wav_path, metadata, inline)
        export = _trusted_export_path(wav_path, metadata, analysis_dir)
        return inline, export if export.is_file() else None
    export = _trusted_export_path(wav_path, metadata, analysis_dir)
    if not export.is_file():
        return None, None
    try:
        document = json.loads(export.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise SavedAnalysisMismatch(f"Could not read saved analysis: {exc}") from exc
    verify_analysis_identity(wav_path, metadata, document)
    return document, export
