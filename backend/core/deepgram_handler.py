"""Deepgram STT handler for streaming transcription."""

import asyncio
from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
from config import get_settings


class DeepgramHandler:
    """Handles streaming speech-to-text via Deepgram."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncDeepgramClient(api_key=settings.deepgram_api_key)
        self.connection = None
        self.connection_context = None
        self.listening_task = None

    async def start_transcription(self, on_transcript_callback):
        """Start a live transcription session.

        Args:
            on_transcript_callback: Async function called with transcript text
        """
        self.on_transcript = on_transcript_callback

        # Connect to Deepgram Flux v2 using async context manager
        self.connection_context = self.client.listen.v2.connect(
            model="flux-general-en",
            encoding="linear16",
            sample_rate=16000,
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
        print("Deepgram connection opened")

    async def _handle_message(self, message):
        """Handle messages from Deepgram."""
        if hasattr(message, 'transcript') and message.transcript:
            is_final = getattr(message, 'is_final', False)
            await self.on_transcript(message.transcript, is_final)

    def _handle_close(self, *args):
        """Handle connection closed event (called by Deepgram)."""
        print("Deepgram connection closed by server")
        # Connection closed by server - cancel our listening task
        if self.listening_task and not self.listening_task.done():
            self.listening_task.cancel()

    def _handle_error(self, error):
        """Handle connection error event."""
        print(f"Deepgram error: {error}")

    async def send_audio(self, audio_data: bytes):
        """Send audio bytes to Deepgram."""
        if self.connection:
            await self.connection._send(audio_data)

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
