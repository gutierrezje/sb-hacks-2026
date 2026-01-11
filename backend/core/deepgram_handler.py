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
    """Handles streaming speech-to-text via Deepgram Flux v2."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncDeepgramClient(api_key=settings.deepgram_api_key)
        self.connection = None
        self.connection_context = None
        self.listening_task = None
        self._on_transcript: Callable[[str, bool], Awaitable[None]] | None = None

    async def start_transcription(
        self,
        on_transcript: Callable[[str, bool], Awaitable[None]],
    ):
        """Start a live transcription session.

        Args:
            on_transcript: Called with (transcript_text, is_final) for each update
        """
        self._on_transcript = on_transcript

        # Connect to Deepgram Flux v2
        self.connection_context = self.client.listen.v2.connect(
            model="flux-general-en",
            encoding="linear16",
            sample_rate="16000",
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
        """Handle messages from Deepgram Flux v2."""
        logger.info(f"Deepgram message: {type(message).__name__}")

        if isinstance(message, ListenV2Connected):
            logger.info(f"Deepgram connected: request_id={message.request_id}")
            return

        if isinstance(message, ListenV2TurnInfo):
            transcript = message.transcript
            is_final = message.event == "EndOfTurn"
            logger.info(f"TurnInfo event={message.event} transcript='{transcript}'")

            if transcript and self._on_transcript:
                await self._on_transcript(transcript, is_final)

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
            logger.debug(f"Sending {len(audio_data)} bytes to Deepgram")
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
