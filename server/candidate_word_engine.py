from __future__ import annotations

from typing import Callable, Iterable

try:
    from server.phoneme_substitution import analyze_substitutions
except ImportError:
    from phoneme_substitution import analyze_substitutions


def _clamp(value: float, low: float = 0.0, high: float = 0.99) -> float:
    return max(low, min(high, float(value)))


def _context_words(context: str) -> set[str]:
    ctx = (context or "").lower()
    if "i see a" in ctx:
        return {"cat", "dog", "ball", "car", "fish", "bird", "house"}
    if "i want" in ctx:
        return {"go", "food", "ball", "car"}
    if "look at the" in ctx:
        return {"cat", "dog", "ball", "car", "house"}
    if "where is the" in ctx:
        return {"cat", "dog", "ball", "car", "house"}
    return set()


def _speaker_word_count(profile: dict, word: str) -> int:
    wh = profile.get("wordHistory", {}) if isinstance(profile, dict) else {}
    if not isinstance(wh, dict):
        return 0
    entry = wh.get(word, 0)
    if isinstance(entry, dict):
        for key in ("approvedCount", "count", "confirmedCount"):
            try:
                return int(entry.get(key, 0) or 0)
            except Exception:
                pass
        return 0
    try:
        return int(entry or 0)
    except Exception:
        return 0


def _mapping_count(profile: dict, observed_text: str, word: str) -> int:
    learned_map = profile.get("heardToMeaning", {}) if isinstance(profile, dict) else {}
    if not isinstance(learned_map, dict):
        return 0
    heard = learned_map.get((observed_text or "").lower(), {})
    if not isinstance(heard, dict):
        return 0
    try:
        return int(heard.get(word, 0) or 0)
    except Exception:
        return 0


def _pattern_count(pattern_history: dict, key: str) -> int:
    try:
        value = pattern_history.get(key, 0)
        if isinstance(value, dict):
            for field in ("approvedCount", "count", "confirmedCount"):
                if field in value:
                    return int(value.get(field, 0) or 0)
            return 0
        return int(value or 0)
    except Exception:
        return 0


def _learned_pattern_evidence(profile: dict, comparison: dict) -> dict:
    """
    Score only directional patterns that match the candidate's expected->observed
    relationship. Because the profile is updated only from approved examples, this
    acts as confirmed speaker-specific evidence rather than a rewrite of observation.
    """
    ph = profile.get("patternHistory", {}) if isinstance(profile, dict) else {}
    if not isinstance(ph, dict):
        ph = {}

    matched = []
    total_count = 0
    weighted_support = 0.0

    for item in comparison.get("substitutions", []) or []:
        if not isinstance(item, dict):
            continue

        expected = str(item.get("expected") or "")
        observed = str(item.get("observed") or "")
        position = str(item.get("position") or "unknown")

        generic_key = f"{expected}->{observed}"
        positional_key = f"{generic_key}@{position}"

        generic_count = _pattern_count(ph, generic_key)
        positional_count = _pattern_count(ph, positional_key)

        # Positional confirmation is more specific and therefore carries more weight.
        effective_count = generic_count + (2 * positional_count)
        if effective_count <= 0:
            continue

        conf = item.get("observedConfidence")
        try:
            conf_weight = max(0.35, min(1.0, float(conf))) if conf is not None else 0.70
        except Exception:
            conf_weight = 0.70

        item_support = effective_count * conf_weight
        weighted_support += item_support
        total_count += effective_count
        matched.append({
            "expected": expected,
            "observed": observed,
            "position": position,
            "genericCount": generic_count,
            "positionalCount": positional_count,
            "effectiveCount": effective_count,
            "observedConfidence": round(conf_weight, 3),
            "weightedSupport": round(item_support, 3),
        })

    # Saturating boost: repeated approved evidence helps, but can never dominate.
    boost = min(0.14, 0.022 * weighted_support)

    return {
        "matchedPatterns": matched,
        "confirmedPatternCount": total_count,
        "weightedSupport": round(weighted_support, 3),
        "boost": round(boost, 3),
        "hasConfirmedPatternSupport": bool(matched),
    }


def rank_candidate_words(
    *,
    words: Iterable[str],
    observed_ipa: str,
    observed_tokens: list[str],
    observed_confidences: list[float],
    observed_text: str,
    context: str,
    profile: dict,
    g2p_ipa: Callable[[str], str],
    tokenize_ipa: Callable[[str], list[str]],
    evidence_scores: Callable,
    combined_confidence: Callable,
    acoustic: dict,
    temporal: dict,
    build_learning_layers: Callable,
    max_results: int = 8,
) -> list[dict]:
    """
    Rank known English candidates using:
      - phoneme edit similarity
      - explicit deletion/substitution/insertion evidence
      - acoustic/temporal evidence
      - context
      - approved speaker history
      - previously confirmed heard->meaning mappings

    The observed phonemes are never rewritten.
    """
    context_words = _context_words(context)
    ranked: list[dict] = []

    for word in words:
        expected_ipa = g2p_ipa(word)
        expected_tokens = tokenize_ipa(expected_ipa)
        if not expected_tokens:
            continue

        comparison = analyze_substitutions(
            expected_tokens,
            observed_tokens,
            learned_patterns=(profile.get("patternHistory", {}) if isinstance(profile, dict) else {}),
            observed_confidences=observed_confidences,
        )

        substitutions = comparison.get("substitutions", []) or []
        deletions = comparison.get("deletions", []) or []
        insertions = comparison.get("insertions", []) or []
        similarity = float(comparison.get("similarity", 0.0) or 0.0)

        # Candidate should remain plausible. This keeps the engine from flooding
        # the UI with unrelated dictionary words while still allowing more than
        # simple initial/final deletion matches.
        if similarity < 0.34:
            continue

        initial_deletion = any(
            isinstance(item, dict) and item.get("position") == "initial"
            for item in deletions
        )
        final_deletion = any(
            isinstance(item, dict) and item.get("position") == "final"
            for item in deletions
        )

        candidate = {
            "word": word,
            "expectedPhonemes": expected_ipa,
            "observedPhonemes": observed_ipa,
            "missingInitial": next(
                (str(item.get("expected") or "") for item in deletions
                 if isinstance(item, dict) and item.get("position") == "initial"),
                ""
            ),
            "missingFinal": next(
                (str(item.get("expected") or "") for item in deletions
                 if isinstance(item, dict) and item.get("position") == "final"),
                ""
            ),
            "possibleInitialOmission": initial_deletion,
            "possibleFinalOmission": final_deletion,
            "phonemeSimilarity": round(similarity, 3),
            "phonemeComparison": comparison,
            "substitutionCount": len(substitutions),
            "deletionCount": len(deletions),
            "insertionCount": len(insertions),
        }

        if initial_deletion and final_deletion:
            candidate["pattern"] = "initial-and-final deletion"
        elif initial_deletion:
            candidate["pattern"] = "initial-consonant deletion"
        elif final_deletion:
            candidate["pattern"] = "final-consonant deletion"
        elif substitutions:
            candidate["pattern"] = "phoneme substitution"
        elif deletions:
            candidate["pattern"] = "phoneme deletion"
        elif insertions:
            candidate["pattern"] = "phoneme insertion"
        else:
            candidate["pattern"] = "phoneme match"

        reasons = []
        if similarity >= 0.80:
            reasons.append("strong phoneme match")
        elif similarity >= 0.60:
            reasons.append("moderate phoneme match")
        else:
            reasons.append("partial phoneme match")
        if deletions:
            reasons.append(f"{len(deletions)} dropped sound(s) fit")
        if substitutions:
            reasons.append(f"{len(substitutions)} changed sound(s) fit")
        if insertions:
            reasons.append(f"{len(insertions)} inserted sound(s) fit")
        if word in context_words:
            reasons.append("matches supplied context")

        ev = evidence_scores(acoustic, temporal, observed_ipa, candidate)
        candidate["evidence"] = ev

        # Existing confidence model remains the base; phoneme similarity and
        # personalization only re-rank around that evidence.
        context_boost = 0.07 if word in context_words else 0.0
        base_conf = float(combined_confidence(ev, context_boost))

        # Similarity bonus is deliberately bounded so it cannot overpower
        # poor acoustic/temporal evidence.
        similarity_boost = max(-0.05, min(0.16, (similarity - 0.50) * 0.30))

        word_count = _speaker_word_count(profile, word)
        word_history_boost = min(0.08, 0.015 * word_count)

        mapping_count = _mapping_count(profile, observed_text, word)
        mapping_boost = min(0.12, 0.03 * mapping_count)

        learned_pattern_evidence = _learned_pattern_evidence(profile, comparison)
        learned_pattern_count = int(learned_pattern_evidence.get("confirmedPatternCount", 0) or 0)
        pattern_boost = float(learned_pattern_evidence.get("boost", 0.0) or 0.0)
        if learned_pattern_evidence.get("hasConfirmedPatternSupport"):
            patterns = learned_pattern_evidence.get("matchedPatterns") or []
            readable = ", ".join(
                f"/{p.get('expected','?')}/→/{p.get('observed','?')}/"
                + (f" ({p.get('position')})" if p.get("position") not in (None, "", "unknown") else "")
                for p in patterns[:3]
            )
            reasons.append(f"confirmed speaker pattern support: {readable}")

        learning_adaptation = build_learning_layers(
            profile=profile,
            candidate=candidate
        ).get("10_speakerAdaptation", {})
        adaptation_boost = float(learning_adaptation.get("adaptationBoost", 0.0) or 0.0)

        final_conf = _clamp(
            base_conf
            + similarity_boost
            + word_history_boost
            + mapping_boost
            + pattern_boost
            + adaptation_boost
        )

        candidate["learningAdaptation"] = learning_adaptation
        candidate["speakerWordHistoryCount"] = word_count
        candidate["personalizedMappingCount"] = mapping_count
        candidate["learnedPatternSupportCount"] = learned_pattern_count
        candidate["learnedSubstitutionEvidence"] = learned_pattern_evidence
        candidate["rankingEvidence"] = {
            "baseEvidenceConfidence": round(base_conf, 3),
            "phonemeSimilarityBoost": round(similarity_boost, 3),
            "contextBoost": round(context_boost, 3),
            "speakerWordHistoryBoost": round(word_history_boost, 3),
            "personalizedMappingBoost": round(mapping_boost, 3),
            "learnedPatternBoost": round(pattern_boost, 3),
            "confirmedPatternWeightedSupport": learned_pattern_evidence.get("weightedSupport", 0.0),
            "speakerAdaptationBoost": round(adaptation_boost, 3),
        }
        candidate["confidence"] = round(final_conf, 3)
        candidate["score"] = round(final_conf, 3)
        candidate["reason"] = "; ".join(reasons)

        if word in context_words:
            candidate["contextMatch"] = True

        ranked.append(candidate)

    ranked.sort(
        key=lambda x: (
            x.get("confidence", 0.0),
            x.get("phonemeSimilarity", 0.0),
            -x.get("deletionCount", 0),
            -x.get("substitutionCount", 0),
        ),
        reverse=True,
    )

    # Preserve multiple candidates when scores are close rather than forcing a
    # single answer. The caller can still use candidate[0] as the leading guess.
    return ranked[:max_results]
