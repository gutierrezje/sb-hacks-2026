"""Deepgram STT handler for streaming transcription using Flux v2."""

import asyncio
import logging
from typing import Callable, Awaitable

from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
from deepgram.listen.v2.types import ListenV2TurnInfo, ListenV2Connected
from config import get_settings


logger = logging.getLogger(__name__)


class DeepgramHandler:
    """Handles streaming speech-to-text via Deepgram Flux v2 with Eager EOT support."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncDeepgramClient(api_key=settings.deepgram_api_key)
        self.connection = None
        self.connection_context = None
        self.listening_task = None
        self._on_transcript: Callable[[str, bool], Awaitable[None]] | None = None
        self._on_eager_eot: Callable[[str], Awaitable[None]] | None = None
        self._on_turn_resumed: Callable[[], Awaitable[None]] | None = None

    async def start_transcription(
        self,
        on_transcript: Callable[[str, bool], Awaitable[None]],
        on_eager_eot: Callable[[str], Awaitable[None]] | None = None,
        on_turn_resumed: Callable[[], Awaitable[None]] | None = None,
    ):
        """Start a live transcription session with Eager EOT support.

        Args:
            on_transcript: Called with (transcript_text, is_final) for each update
            on_eager_eot: Called with transcript when Deepgram is moderately confident user finished
            on_turn_resumed: Called when user continues speaking after eager EOT
        """
        self._on_transcript = on_transcript
        self._on_eager_eot = on_eager_eot
        self._on_turn_resumed = on_turn_resumed

        # Connect to Deepgram Flux v2 with Eager EOT enabled
        self.connection_context = self.client.listen.v2.connect(
            model="flux-general-en",
            encoding="linear16",
            sample_rate="16000",
            eot_threshold="0.7",  # Balanced threshold for reliable final EOT
            eager_eot_threshold="0.55",  # Trigger early LLM processing - tunable
            eot_timeout_ms="6000",  # Reduced from 7000ms for faster response
        )
        self.connection = await self.connection_context.__aenter__()

        # Set up event handlers
        self.connection.on(EventType.OPEN, self._handle_open)
        self.connection.on(EventType.MESSAGE, self._handle_message)
        self.connection.on(EventType.CLOSE, self._handle_close)
        self.connection.on(EventType.ERROR, self._handle_error)

        # Start listening task in background
        self.listening_task = asyncio.create_task(self.connection.start_listening())

    def _handle_open(self, *args):
        """Handle connection opened event."""
        logger.info("Deepgram connection opened")

    async def _handle_message(self, message):
        """Handle messages from Deepgram Flux v2 including Eager EOT events."""
        if isinstance(message, ListenV2Connected):
            logger.info(f"Deepgram connected: request_id={message.request_id}")
            return

        if isinstance(message, ListenV2TurnInfo):
            transcript = message.transcript
            event_type = message.event

            # Handle different turn events
            if event_type == "EagerEndOfTurn":
                # Deepgram is moderately confident user finished - start speculative processing
                logger.debug(f"Eager EOT triggered: '{transcript}'")
                if transcript and self._on_eager_eot:
                    await self._on_eager_eot(transcript)
                # Still send to transcript handler for UI updates
                if transcript and self._on_transcript:
                    await self._on_transcript(transcript, is_final=False)

            elif event_type == "TurnResumed":
                # User continued speaking - cancel speculative work
                logger.debug("Turn resumed - user continued speaking")
                if self._on_turn_resumed:
                    await self._on_turn_resumed()

            elif event_type == "EndOfTurn":
                # High confidence final transcript - finalize response
                logger.debug(f"Final EOT: '{transcript}'")
                if transcript and self._on_transcript:
                    await self._on_transcript(transcript, is_final=True)

            elif transcript:
                # Regular interim transcript
                if self._on_transcript:
                    await self._on_transcript(transcript, is_final=False)
            else:
                logger.debug(f"Received empty transcript for event: {event_type}")

    def _handle_close(self, *args):
        """Handle connection closed event."""
        logger.info("Deepgram connection closed")
        if self.listening_task and not self.listening_task.done():
            self.listening_task.cancel()

    def _handle_error(self, error):
        """Handle connection error event."""
        logger.error(f"Deepgram error: {error}")

    async def send_audio(self, audio_data: bytes):
        """Send audio bytes to Deepgram for transcription."""
        if self.connection:
            await self.connection.send_media(audio_data)

    async def close(self):
        """Close the transcription connection."""
        if self.listening_task:
            self.listening_task.cancel()
            try:
                await self.listening_task
            except asyncio.CancelledError:
                pass

        if self.connection_context:
            await self.connection_context.__aexit__(None, None, None)
            self.connection = None
            self.connection_context = None
