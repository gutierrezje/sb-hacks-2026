"""Timing utilities for measuring latency in the conversational pipeline."""

import time
import logging
from typing import Dict, List
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


@dataclass
class TimingEvent:
    """Represents a single timing measurement."""
    name: str
    start_time: float
    end_time: float | None = None

    @property
    def duration_ms(self) -> float | None:
        """Get duration in milliseconds."""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000


@dataclass
class PipelineMetrics:
    """Collects timing metrics for a complete conversational turn."""
    session_id: str
    turn_id: str
    events: List[TimingEvent] = field(default_factory=list)
    metadata: Dict[str, any] = field(default_factory=dict)

    def start_event(self, name: str) -> TimingEvent:
        """Start timing an event.

        Args:
            name: Event identifier (e.g., "stt", "llm", "tts")

        Returns:
            The timing event that was started
        """
        event = TimingEvent(name=name, start_time=time.perf_counter())
        self.events.append(event)
        return event

    def end_event(self, name: str):
        """End timing for the most recent event with this name.

        Args:
            name: Event identifier to end
        """
        # Find the most recent event with this name that hasn't ended
        for event in reversed(self.events):
            if event.name == name and event.end_time is None:
                event.end_time = time.perf_counter()
                return

        logger.warning(f"No active event found with name: {name}")

    def get_duration(self, name: str) -> float | None:
        """Get duration of a completed event in milliseconds.

        Args:
            name: Event identifier

        Returns:
            Duration in ms, or None if not found/incomplete
        """
        for event in self.events:
            if event.name == name and event.end_time is not None:
                return event.duration_ms
        return None

    def get_total_duration(self) -> float | None:
        """Get total duration from first event start to last event end.

        Returns:
            Total duration in ms, or None if no complete events
        """
        if not self.events:
            return None

        completed_events = [e for e in self.events if e.end_time is not None]
        if not completed_events:
            return None

        start = min(e.start_time for e in self.events)
        end = max(e.end_time for e in completed_events)
        return (end - start) * 1000

    def log_summary(self):
        """Log a summary of all timing metrics."""
        logger.info(f"=== Timing Summary [{self.session_id}:{self.turn_id}] ===")

        for event in self.events:
            if event.duration_ms is not None:
                logger.info(f"  {event.name}: {event.duration_ms:.2f}ms")
            else:
                logger.warning(f"  {event.name}: INCOMPLETE")

        total = self.get_total_duration()
        if total:
            logger.info(f"  TOTAL: {total:.2f}ms")

        if self.metadata:
            logger.info(f"  Metadata: {self.metadata}")


class TimingManager:
    """Manages timing metrics for multiple concurrent sessions/turns."""

    def __init__(self):
        self._metrics: Dict[str, PipelineMetrics] = {}

    def create_metrics(self, session_id: str, turn_id: str, **metadata) -> PipelineMetrics:
        """Create a new metrics tracker for a turn.

        Args:
            session_id: Session identifier
            turn_id: Turn identifier (unique within session)
            **metadata: Additional context (e.g., transcript length, model version)

        Returns:
            PipelineMetrics instance
        """
        key = f"{session_id}:{turn_id}"
        metrics = PipelineMetrics(
            session_id=session_id,
            turn_id=turn_id,
            metadata=metadata
        )
        self._metrics[key] = metrics
        return metrics

    def get_metrics(self, session_id: str, turn_id: str) -> PipelineMetrics | None:
        """Get existing metrics for a turn."""
        key = f"{session_id}:{turn_id}"
        return self._metrics.get(key)

    def cleanup_metrics(self, session_id: str, turn_id: str):
        """Remove metrics after logging/storing."""
        key = f"{session_id}:{turn_id}"
        self._metrics.pop(key, None)


@asynccontextmanager
async def time_block(metrics: PipelineMetrics, event_name: str):
    """Context manager for timing a block of code.

    Usage:
        async with time_block(metrics, "llm"):
            response = await llm.generate_response(...)
    """
    metrics.start_event(event_name)
    try:
        yield
    finally:
        metrics.end_event(event_name)
