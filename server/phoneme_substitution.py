from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Edit:
    kind: str
    expected: str | None
    observed: str | None
    expected_index: int | None
    observed_index: int | None


def _normalize(seq) -> list[str]:
    if seq is None:
        return []
    if isinstance(seq, str):
        parts = [p for p in seq.strip().split() if p]
        return parts if len(parts) > 1 else list(seq.strip())
    return [str(x) for x in seq if str(x).strip()]


def align_phonemes(expected, observed) -> list[Edit]:
    a = _normalize(expected)
    b = _normalize(observed)
    n, m = len(a), len(b)

    dp = [[0] * (m + 1) for _ in range(n + 1)]
    op = [[None] * (m + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        dp[i][0] = i
        op[i][0] = "delete"
    for j in range(1, m + 1):
        dp[0][j] = j
        op[0][j] = "insert"

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            same = a[i - 1] == b[j - 1]
            choices = [
                (dp[i - 1][j - 1] + (0 if same else 1), "match" if same else "substitute"),
                (dp[i - 1][j] + 1, "delete"),
                (dp[i][j - 1] + 1, "insert"),
            ]
            dp[i][j], op[i][j] = min(choices, key=lambda x: x[0])

    edits: list[Edit] = []
    i, j = n, m
    while i > 0 or j > 0:
        action = op[i][j]
        if action in ("match", "substitute"):
            if action == "substitute":
                edits.append(Edit("substitution", a[i - 1], b[j - 1], i - 1, j - 1))
            i -= 1
            j -= 1
        elif action == "delete":
            edits.append(Edit("deletion", a[i - 1], None, i - 1, None))
            i -= 1
        else:
            edits.append(Edit("insertion", None, b[j - 1], None, j - 1))
            j -= 1

    edits.reverse()
    return edits


def _position(index: int | None, length: int) -> str:
    if index is None or length <= 0:
        return "unknown"
    if index == 0:
        return "initial"
    if index == length - 1:
        return "final"
    return "medial"


def analyze_substitutions(expected, observed, learned_patterns: dict | None = None) -> dict:
    expected_seq = _normalize(expected)
    observed_seq = _normalize(observed)
    edits = align_phonemes(expected_seq, observed_seq)

    learned_patterns = learned_patterns or {}
    substitutions = []
    deletions = []
    insertions = []

    for edit in edits:
        if edit.kind == "substitution":
            key = f"{edit.expected}->{edit.observed}"
            repetitions = int(learned_patterns.get(key, 0) or 0)
            substitutions.append({
                "expected": edit.expected,
                "observed": edit.observed,
                "position": _position(edit.expected_index, len(expected_seq)),
                "expectedIndex": edit.expected_index,
                "observedIndex": edit.observed_index,
                "learnedPatternCount": repetitions,
                "knownSpeakerPattern": repetitions > 0,
            })
        elif edit.kind == "deletion":
            deletions.append({
                "expected": edit.expected,
                "position": _position(edit.expected_index, len(expected_seq)),
                "expectedIndex": edit.expected_index,
            })
        elif edit.kind == "insertion":
            insertions.append({
                "observed": edit.observed,
                "observedIndex": edit.observed_index,
            })

    distance = len(edits)
    denom = max(1, len(expected_seq), len(observed_seq))
    similarity = max(0.0, 1.0 - (distance / denom))

    return {
        "expectedPhonemes": expected_seq,
        "observedPhonemes": observed_seq,
        "substitutions": substitutions,
        "deletions": deletions,
        "insertions": insertions,
        "editCount": distance,
        "similarity": round(similarity, 3),
    }
