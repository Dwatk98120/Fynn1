"""Caregiver-friendly word-review labels and safety checks.

Pure Python: tests run without audio models, a display, or Tkinter.
Persisted review statuses are unchanged for backward compatibility.
"""
from __future__ import annotations

import re

DECISION_TO_STATUS = {
    "Not reviewed": "not_reviewed",
    "Confirm": "confirmed",
    "Unsure": "boundary_uncertain",
    "Reject": "rejected",
}
STATUS_TO_DECISION = {status: label for label, status in DECISION_TO_STATUS.items()}


def display_decision(saved_status: str) -> str:
    """Read existing and new review files without rewriting their statuses."""
    return STATUS_TO_DECISION.get(saved_status, "Not reviewed")


def confirmation_issue(label: str, *, boundary_uncertain: bool, adult_reference: bool = False) -> str | None:
    """Return a specific block reason before any learning clip is exported."""
    if adult_reference:
        return "adult_reference"
    word = label.strip().lower()
    if not word:
        return "missing_word"
    if len(word.split()) > 1:
        return "multiple_words"
    if not re.fullmatch(r"[a-z][a-z'-]*", word):
        return "invalid_word"
    if boundary_uncertain:
        return "unclear_boundary"
    return None


def caregiver_explanation(reason: str, word_number: int, label: str) -> str:
    """Explain exactly what action is available, without inviting a guess."""
    prefix = f"Please check Word {word_number}.\n\n"
    if reason == "adult_reference":
        return (prefix + "This recording is marked as an adult test. Adult examples cannot be confirmed "
                "for child-specific learning. Use the Reference Audio Library for adult examples.")
    if reason == "missing_word":
        return (prefix + "No word has been entered. Play the clip and enter the word you hear. "
                "If you can't identify it confidently, choose Unsure.")
    if reason == "multiple_words":
        return (prefix + "You entered more than one word. Each clip can be confirmed as only one word. "
                "Play the clip and check it. If it contains multiple words, choose Unsure "
                "rather than guessing which part belongs to this clip.")
    if reason == "invalid_word":
        return (prefix + "Enter one word using letters (apostrophes or hyphens are okay). "
                "If the word isn't clear, choose Unsure. Don't guess just to save.")
    if reason == "unclear_boundary":
        suffix = f' The word entered is "{label.strip()}".' if label.strip() else ""
        return (prefix + "Hearlium cannot reliably tell where this clip starts or ends." + suffix +
                " Playing the clip does not remove this warning. "
                "Choose Unsure to save your review without approving this clip for learning. "
                "It can be confirmed only after its boundaries are corrected and verified.")
    raise ValueError(f"Unknown review issue: {reason}")
