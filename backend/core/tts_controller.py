"""Deepgram TTS (Aura) controller for text-to-speech with streaming optimization."""

from typing import AsyncIterator
from deepgram import AsyncDeepgramClient
from config import get_settings


class TTSController:
    """Handles text-to-speech via Deepgram Aura with optimized streaming."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncDeepgramClient(api_key=settings.deepgram_api_key)

    async def synthesize(self, text: str) -> bytes:
        """Convert text to speech audio (non-streaming, legacy).

        Args:
            text: The text to convert to speech

        Returns:
            Audio bytes (linear16 PCM at 16kHz)
        """
        audio_chunks = []
        async for chunk in self.synthesize_stream(text):
            audio_chunks.append(chunk)
        return b"".join(audio_chunks)

    async def synthesize_stream(self, text: str) -> AsyncIterator[bytes]:
        """Stream TTS audio chunks as they arrive from Deepgram.

        This enables playing audio while synthesis is still in progress,
        dramatically reducing perceived latency.

        Args:
            text: The text to convert to speech

        Yields:
            Audio chunk bytes (linear16 PCM at 16kHz)

        Note:
            Client should start playing audio as soon as first chunk arrives.
            Chunk size is optimized by Deepgram for low-latency streaming.
        """
        # Use optimized settings for minimal latency
        response = self.client.speak.v1.audio.generate(
            text=text,
            model="aura-2-neptune-en",  # Fast, natural model
            encoding="linear16",         # Quality encoding
            sample_rate=16000,           # Match STT sample rate
        )

        # Stream chunks as they arrive - don't wait for full synthesis
        async for chunk in response:
            yield chunk
