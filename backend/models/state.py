"""Marcus's internal state model."""

from enum import Enum
from pydantic import BaseModel, field_validator


class EmotionalState(str, Enum):
    """Marcus's emotional state that maps to emoji avatar."""

    NEUTRAL = "neutral"
    IMPRESSED = "impressed"
    VERY_IMPRESSED = "very_impressed"
    SKEPTICAL = "skeptical"
    STRESSED = "stressed"
    DONE = "done"


class MarcusState(BaseModel):
    """Marcus's internal state during negotiation."""

    patience: int = 100
    emotional_state: EmotionalState = EmotionalState.NEUTRAL
    budget_ceiling: int = 150_000
    current_offer: int | None = None

    @field_validator("current_offer")
    @classmethod
    def validate_offer(cls, v, info):
        if v is not None and "budget_ceiling" in info.data:
            budget = info.data["budget_ceiling"]
            if v > budget:
                raise ValueError(f"Offer {v} exceeds budget ceiling {budget}")
        return v
