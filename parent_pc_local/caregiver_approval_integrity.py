"""Phase 3 review/approval concurrency protections.

No acoustic observation or WAV is ever modified here. Every learning decision
must be backed by a verified result for the exact selected recording.
"""
from __future__ import annotations

from pathlib import Path

from analysis_consistency import (
    SavedAnalysisMismatch, load_verified_saved_analysis, observation_id,
)


class ReviewDecisionSuperseded(RuntimeError):
    """An API reply was accepted after another review/analysis became current."""

    def __init__(self, observation: str, revision: int):
        self.observation = observation
        self.revision = revision
        super().__init__(f"observation={observation!r}; decision_revision={revision}")


def review_revision(metadata: dict) -> int:
    """Monotonically advance a recording's local caregiver decision version."""
    try:
        value = int(metadata.get("reviewRevision") or 0)
    except (TypeError, ValueError):
        value = 0
    return max(value, 0)


def require_verified_loaded_analysis(
    wav_path: Path, metadata: dict, loaded_result: object, analysis_directory: Path,
) -> str:
    """Require the displayed result to be the VERIFIED, current saved result.

    A metadata observation ID by itself is never proof that the caregiver has
    loaded the associated speech observations into the review window.
    """
    if not wav_path.is_file():
        raise ValueError("The recording is missing. Load an existing recording first.")
    if not isinstance(loaded_result, dict):
        raise ValueError("No verified analysis is loaded. Load and review the saved analysis, or analyze this recording again before saving feedback.")
    try:
        saved, _ = load_verified_saved_analysis(wav_path, metadata, analysis_directory)
    except SavedAnalysisMismatch as exc:
        raise ValueError(f"The saved analysis cannot be verified: {exc}. Please analyze the recording again.") from exc
    if not isinstance(saved, dict) or saved != loaded_result:
        raise ValueError("The loaded analysis is missing or no longer matches this recording's saved observations. Reload the recording before saving feedback.")
    oid = observation_id(saved)
    if not oid:
        raise ValueError("The verified analysis has no observation ID. Reanalyze before saving feedback.")
    return oid
