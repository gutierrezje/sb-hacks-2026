"""WebSocket endpoint for salary negotiation sessions."""

import json
import logging
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from pathlib import Path

from core.deepgram_handler import DeepgramHandler
from core.llm_client import LLMClient
from core.tts_controller import TTSController
from core.timing import TimingManager, time_block
from models.session import NegotiationSession
from store.sessions import session_store


logger = logging.getLogger(__name__)
router = APIRouter()

# Load Marcus system prompt
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "marcus.txt"
MARCUS_PROMPT = PROMPT_PATH.read_text()


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
    timing_manager = TimingManager()
    turn_counter = 0

    logger.info(f"New WebSocket connection: {session_id}")

    try:
        await websocket.accept()

        # Create session
        session = NegotiationSession(session_id=session_id)
        session_store[session_id] = session

        # Set up components
        deepgram_handler = DeepgramHandler()
        llm = LLMClient()
        tts = TTSController()

        async def on_transcript(text: str, is_final: bool):
            """Handle transcript and generate LLM response if final."""
            nonlocal turn_counter

            # Send transcript to frontend
            await websocket.send_json({
                "type": "transcript",
                "text": text,
                "is_final": is_final,
            })

            # If final transcript, generate LLM response and speak it
            if is_final and text.strip():
                turn_counter += 1
                turn_id = f"turn_{turn_counter}"

                # Create metrics for this turn
                metrics = timing_manager.create_metrics(
                    session_id=session_id,
                    turn_id=turn_id,
                    transcript_length=len(text),
                )

                # Start overall pipeline timing
                metrics.start_event("pipeline_total")

                # Generate LLM response
                async with time_block(metrics, "llm_generation"):
                    llm_response = await llm.generate_response(
                        user_message=text,
                        system_prompt=MARCUS_PROMPT,
                    )

                # Add response length to metadata
                metrics.metadata["response_length"] = len(llm_response)

                # Convert to speech and send
                async with time_block(metrics, "tts_synthesis"):
                    audio_bytes = await tts.synthesize(llm_response)

                metrics.metadata["audio_bytes"] = len(audio_bytes)

                async with time_block(metrics, "network_send"):
                    await websocket.send_bytes(audio_bytes)

                # End overall timing and log
                metrics.end_event("pipeline_total")
                metrics.log_summary()

                # Cleanup metrics
                timing_manager.cleanup_metrics(session_id, turn_id)

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
                    
                elif data.get("type") == "test_llm":
                    # Test full LLM -> TTS pipeline
                    user_text = data.get("text", "")
                    if user_text.strip():
                        llm_response = await llm.generate_response(
                            user_message=user_text,
                            system_prompt=MARCUS_PROMPT,
                        )
                        audio_bytes = await tts.synthesize(llm_response)
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
