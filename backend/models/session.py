"""Session models for negotiation state."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NegotiationSession:
    """Active negotiation session state."""
    
    session_id: str
    started_at: datetime = field(default_factory=datetime.utcnow)
