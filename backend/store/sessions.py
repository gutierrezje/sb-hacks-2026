"""In-memory session storage."""

from models.session import NegotiationSession


# Simple in-memory storage
session_store: dict[str, NegotiationSession] = {}
