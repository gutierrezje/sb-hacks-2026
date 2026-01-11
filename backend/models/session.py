"""Session models for negotiation state."""

from enum import Enum
from pydantic import BaseModel, Field

from models.state import MarcusState


class NegotiationOutcome(str, Enum):
    """Final outcome of negotiation."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    HUNG_UP = "hung_up"


class NegotiationSession(BaseModel):
    """Active negotiation session state."""

    session_id: str
    marcus_state: MarcusState = Field(default_factory=MarcusState)
    conversation_history: list[dict] = Field(default_factory=list)
    outcome: NegotiationOutcome | None = None
