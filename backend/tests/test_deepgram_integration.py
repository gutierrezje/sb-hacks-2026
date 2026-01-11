"""Integration test for Deepgram handler with real connection."""

import asyncio
import pytest
from core.deepgram_handler import DeepgramHandler


@pytest.mark.asyncio
async def test_deepgram_full_lifecycle():
    """Test the full lifecycle: connect -> send audio -> receive events -> close."""

    events_received = {
        'open': False,
        'message': False,
        'close': False,
        'error': False
    }

    async def on_transcript(text, is_final):
        """Track if we receive any transcripts."""
        events_received['message'] = True
        print(f"Transcript: {text} (final={is_final})")

    handler = DeepgramHandler()

    # Monkey-patch event handlers to track what events fire
    original_open = handler._handle_open
    original_close = handler._handle_close
    original_error = handler._handle_error

    def track_open(*args):
        events_received['open'] = True
        original_open(*args)

    def track_close(*args):
        events_received['close'] = True
        original_close(*args)

    def track_error(*args):
        events_received['error'] = True
        original_error(*args)

    handler._handle_open = track_open
    handler._handle_close = track_close
    handler._handle_error = track_error

    try:
        # Start connection
        await handler.start_transcription(on_transcript)

        # Wait for OPEN event
        await asyncio.sleep(1)

        # Verify connection opened
        assert events_received['open'], "Connection OPEN event did not fire"
        assert handler.connection is not None, "Connection not established"
        assert handler.listening_task is not None, "Listening task not started"

        # Send some audio (silent audio, won't produce transcript but tests the flow)
        silent_audio = b'\x00\x00' * 8000  # 1 second of silence at 16kHz
        await handler.send_audio(silent_audio)

        # Wait a bit for any responses
        await asyncio.sleep(2)

        # Verify no errors occurred
        assert not events_received['error'], "Error event fired unexpectedly"

        print("All lifecycle events verified")

    finally:
        # Clean up
        await handler.close()

        # Give it a moment to close
        await asyncio.sleep(0.5)


if __name__ == "__main__":
    asyncio.run(test_deepgram_full_lifecycle())
