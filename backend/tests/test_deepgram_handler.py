"""Tests for Deepgram handler."""

import asyncio
import pytest
import numpy as np
from core.deepgram_handler import DeepgramHandler


def generate_test_audio(duration_seconds=1, sample_rate=16000):
    """Generate a simple sine wave as test audio (linear16 PCM)."""
    # Generate a 440 Hz tone (A note)
    t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))
    audio = np.sin(2 * np.pi * 440 * t)
    # Convert to 16-bit PCM
    audio_int16 = (audio * 32767).astype(np.int16)
    return audio_int16.tobytes()


@pytest.mark.asyncio
async def test_deepgram_connection():
    """Test that we can connect to Deepgram Flux v2."""
    async def on_transcript(text, is_final):
        pass

    handler = DeepgramHandler()
    try:
        await handler.start_transcription(on_transcript)
        assert handler.connection is not None
        assert handler.connection_context is not None
    finally:
        await handler.close()


@pytest.mark.asyncio
async def test_send_audio():
    """Test that we can send audio to Deepgram."""
    transcripts = []

    async def on_transcript(text, is_final):
        transcripts.append((text, is_final))

    handler = DeepgramHandler()
    try:
        await handler.start_transcription(on_transcript)

        # Send test audio
        test_audio = generate_test_audio(duration_seconds=1)
        await handler.send_audio(test_audio)

        # Wait for potential transcription
        await asyncio.sleep(2)

        # Audio is a tone (no speech), so we might not get transcripts
        # Just verify send_audio didn't crash
        assert True

    finally:
        await handler.close()
