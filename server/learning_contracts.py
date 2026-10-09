"""
First Sound Helper — Observation / Interpretation / Learning contracts.

Design rule:
- ObservationRecord is immutable evidence from the recording/model.
- InterpretationRecord contains revisable AI conclusions.
- LearningAnnotation contains the five learning keys and references the
  observation_id; it never mutates the observation.
"""
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4
import copy

LEARNING_KEYS = (
    "human_feedback",
    "speaker_adaptation",
    "pattern_learning",
    "strategy_learning",
    "ai_self_evaluation",
)

def _now():
    return datetime.now(timezone.utc).isoformat()

@dataclass(frozen=True)
class ObservationRecord:
    observation_id: str
    observed_at: str
    audio_quality: Dict[str, Any]
    acoustic: Dict[str, Any]
    phonemes: Dict[str, Any]
    temporal: Dict[str, Any]
    raw_model_output: Any = None

    def to_dict(self):
        # Deep-copy nested structures before exposing them.
        return copy.deepcopy(asdict(self))

@dataclass
class InterpretationRecord:
    interpretation_id: str
    observation_id: str
    created_at: str
    candidate_words: list = field(default_factory=list)
    likely_interpretation: Optional[str] = None
    confidence: Optional[float] = None
    uncertainty: Optional[str] = None
    context: Optional[str] = None
    rationale: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return copy.deepcopy(asdict(self))

@dataclass
class LearningAnnotation:
    learning_id: str
    observation_id: str
    created_at: str
    human_feedback: Dict[str, Any] = field(default_factory=dict)
    speaker_adaptation: Dict[str, Any] = field(default_factory=dict)
    pattern_learning: Dict[str, Any] = field(default_factory=dict)
    strategy_learning: Dict[str, Any] = field(default_factory=dict)
    ai_self_evaluation: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return copy.deepcopy(asdict(self))

def new_observation(audio_quality, acoustic, phonemes, temporal, raw_model_output=None):
    return ObservationRecord(
        observation_id=str(uuid4()),
        observed_at=_now(),
        audio_quality=copy.deepcopy(audio_quality),
        acoustic=copy.deepcopy(acoustic),
        phonemes=copy.deepcopy(phonemes),
        temporal=copy.deepcopy(temporal),
        raw_model_output=copy.deepcopy(raw_model_output),
    )

def new_interpretation(observation_id, **kwargs):
    return InterpretationRecord(
        interpretation_id=str(uuid4()),
        observation_id=observation_id,
        created_at=_now(),
        **kwargs,
    )

def new_learning_annotation(observation_id):
    return LearningAnnotation(
        learning_id=str(uuid4()),
        observation_id=observation_id,
        created_at=_now(),
    )
