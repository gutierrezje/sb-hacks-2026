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
    """Marcus's internal state during negotiation.
    
    Respect is a 5-point scale (0-4) that maps to emotional states:
    - 4: Very impressed (exceptional preparation)
    - 3: Impressed (good arguments, data-driven)
    - 2: Neutral (starting state, routine conversation)
    - 1: Stressed (rambling, unrealistic demands)
    - 0: Done (respect exhausted, ends negotiation)
    """

    respect: int = 2  # Start neutral
    emotional_state: EmotionalState = EmotionalState.NEUTRAL
    budget_ceiling: int = 150_000
    current_offer: int | None = None

    @field_validator("respect")
    @classmethod
    def validate_respect(cls, v):
        if not 0 <= v <= 4:
            raise ValueError(f"Respect must be 0-4, got {v}")
        return v

    @field_validator("current_offer")
    @classmethod
    def validate_offer(cls, v, info):
        if v is not None and "budget_ceiling" in info.data:
            budget = info.data["budget_ceiling"]
            if v > budget:
                raise ValueError(f"Offer {v} exceeds budget ceiling {budget}")
        return v
