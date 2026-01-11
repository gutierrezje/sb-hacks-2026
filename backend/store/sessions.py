"""In-memory session storage."""

from models.session import NegotiationSession


# Simple in-memory storage for now, but in production use Redis or similar
session_store: dict[str, NegotiationSession] = {}
