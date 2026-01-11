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
async def test_tts_empty_text():
    """Test TTS with empty text."""
    tts = TTSController()
    
    audio_bytes = await tts.synthesize("")
    
    # Should still return something (even if minimal)
    assert audio_bytes is not None
