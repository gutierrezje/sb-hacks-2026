"""Test TTS controller."""

import pytest
from core.tts_controller import TTSController


@pytest.mark.asyncio
async def test_tts_synthesis():
    """Test basic TTS audio generation."""
    tts = TTSController()
    
    text = "Hello, this is a test."
    audio_bytes = await tts.synthesize(text)
    
    assert audio_bytes is not None
    assert len(audio_bytes) > 0
    assert len(audio_bytes) > 1000  # Should be substantial audio data


@pytest.mark.asyncio
async def test_tts_short_text():
    """Test TTS with short text."""
    tts = TTSController()
    
    # Deepgram requires at least some text, so use a minimal valid input
    audio_bytes = await tts.synthesize("Hi")
    
    assert audio_bytes is not None
    assert len(audio_bytes) > 0
