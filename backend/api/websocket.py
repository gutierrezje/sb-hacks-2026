"""WebSocket endpoint for salary negotiation sessions."""

import json
import logging
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.deepgram_handler import DeepgramHandler
from core.tts_controller import TTSController
from models.session import NegotiationSession
from store.sessions import session_store


logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/negotiate")
async def negotiate_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time salary negotiation.

    Message Protocol:
        Client -> Server:
            - Binary: PCM audio chunks (16-bit, 16kHz, mono)
            - JSON: {"type": "end_session"}
            - JSON: {"type": "test_tts", "text": "..."}

        Server -> Client:
            - JSON: {"type": "transcript", "text": "...", "is_final": bool}
            - Binary: Audio bytes (for TTS responses)
    """
    session_id = str(uuid4())
    deepgram_handler = None

    logger.info(f"New WebSocket connection: {session_id}")

    try:
        await websocket.accept()

        # Create session
        session = NegotiationSession(session_id=session_id)
        session_store[session_id] = session

        # Set up Deepgram STT
        deepgram_handler = DeepgramHandler()

        async def on_transcript(text: str, is_final: bool):
            """Send transcript to frontend."""
            await websocket.send_json({
                "type": "transcript",
                "text": text,
                "is_final": is_final,
            })

        await deepgram_handler.start_transcription(on_transcript=on_transcript)

        # Send ready message
        await websocket.send_json({
            "type": "session_init",
            "session_id": session_id,
        })

        # Main loop: receive audio and forward to Deepgram
        while True:
            message = await websocket.receive()

            if "bytes" in message:
                await deepgram_handler.send_audio(message["bytes"])

            elif "text" in message:
                data = json.loads(message["text"])
                
                if data.get("type") == "end_session":
                    break
                    
                elif data.get("type") == "test_tts":
                    # Test TTS with provided text
                    tts = TTSController()
                    text = data.get("text", "Hello, this is a test.")
                    audio_bytes = await tts.synthesize(text)
                    await websocket.send_bytes(audio_bytes)

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {session_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)

    finally:
        if deepgram_handler:
            await deepgram_handler.close()
        if session_id in session_store:
            del session_store[session_id]
