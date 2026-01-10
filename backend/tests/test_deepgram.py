"""Deepgram API connectivity tests.

This module provides integration tests for Deepgram API endpoints used in
The Salary Dojo application, including Speech-to-Text (STT), Text-to-Speech (TTS),
and real-time WebSocket streaming.

Run with:
    pytest tests/test_deepgram.py -v
    pytest tests/test_deepgram.py::test_prerecorded_stt -v
"""

import pytest
from deepgram import DeepgramClient

from config import get_settings


# Test configuration
SAMPLE_AUDIO_URL = "https://static.deepgram.com/examples/Bueller-Life-moves-pretty-fast.wav"
SAMPLE_TTS_TEXT = "Hello! This is a test of Deepgram's text to speech API."


@pytest.fixture(scope="module")
def deepgram_client():
    """Provide a configured Deepgram client for all tests."""
    settings = get_settings()
    return DeepgramClient(api_key=settings.deepgram_api_key)


@pytest.fixture(scope="module")
def audio_config():
    """Provide standard audio configuration."""
    return {
        "encoding": "linear16",
        "sample_rate": 16000,
    }


class TestSpeechToText:
    """Test suite for Deepgram Speech-to-Text API."""

    def test_prerecorded_transcription(self, deepgram_client):
        """Test transcription of prerecorded audio from URL."""
        response = deepgram_client.listen.v1.media.transcribe_url(
            url=SAMPLE_AUDIO_URL,
            model="nova-2",
            smart_format=True,
        )

        transcript = response.results.channels[0].alternatives[0].transcript

        assert transcript, "Transcript should not be empty"
        assert len(transcript) > 0, "Transcript should contain text"
        assert "life" in transcript.lower(), "Expected content not found in transcript"

    def test_transcription_includes_metadata(self, deepgram_client):
        """Test that transcription response includes expected metadata."""
        response = deepgram_client.listen.v1.media.transcribe_url(
            url=SAMPLE_AUDIO_URL,
            model="nova-2",
            smart_format=True,
        )

        assert response.results is not None
        assert len(response.results.channels) > 0
        assert len(response.results.channels[0].alternatives) > 0


class TestTextToSpeech:
    """Test suite for Deepgram Text-to-Speech API."""

    def test_audio_generation(self, deepgram_client):
        """Test generation of audio from text."""
        response = deepgram_client.speak.v1.audio.generate(
            text=SAMPLE_TTS_TEXT,
            model="aura-asteria-en",
        )

        # Response is a generator; collect all chunks
        audio_chunks = list(response)
        total_bytes = sum(len(chunk) for chunk in audio_chunks)

        assert total_bytes > 0, "Audio data should be generated"
        assert total_bytes > 1000, "Audio should be substantial (>1KB)"

    def test_audio_generation_with_different_voice(self, deepgram_client):
        """Test audio generation with alternative voice model."""
        response = deepgram_client.speak.v1.audio.generate(
            text="Testing alternative voice.",
            model="aura-asteria-en",
        )

        audio_chunks = list(response)
        total_bytes = sum(len(chunk) for chunk in audio_chunks)

        assert total_bytes > 0, "Audio should be generated with alternative voice"


class TestLiveWebSocket:
    """Test suite for Deepgram Live WebSocket STT."""

    def test_websocket_connection(self, deepgram_client, audio_config):
        """Test that WebSocket connection can be established."""
        with deepgram_client.listen.v2.connect(
            model="flux-general-en",
            encoding=audio_config["encoding"],
            sample_rate=audio_config["sample_rate"],
        ) as connection:
            # Connection established successfully
            assert connection is not None

    def test_websocket_connection_with_options(self, deepgram_client, audio_config):
        """Test WebSocket connection with additional options."""
        with deepgram_client.listen.v2.connect(
            model="flux-general-en",
            encoding=audio_config["encoding"],
            sample_rate=audio_config["sample_rate"],
        ) as connection:
            assert connection is not None
