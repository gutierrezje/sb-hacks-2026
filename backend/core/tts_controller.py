"""Deepgram TTS (Aura) controller for text-to-speech."""

from deepgram import AsyncDeepgramClient
from config import get_settings


class TTSController:
    """Handles text-to-speech via Deepgram Aura."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncDeepgramClient(api_key=settings.deepgram_api_key)

    async def synthesize(self, text: str) -> bytes:
        """Convert text to speech audio.

        Args:
            text: The text to convert to speech

        Returns:
            Audio bytes (linear16 PCM at 16kHz)
        """
        response = self.client.speak.v1.audio.generate(
            text=text,
            model="aura-2-neptune-en",
        )
        
        # Collect all audio chunks from async generator
        audio_chunks = []
        async for chunk in response:
            audio_chunks.append(chunk)
        
        return b"".join(audio_chunks)
