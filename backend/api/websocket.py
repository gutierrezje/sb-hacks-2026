"""WebSocket endpoint for salary negotiation sessions."""

import asyncio
import json
import logging
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from pathlib import Path

from core.deepgram_handler import DeepgramHandler
from core.tts_controller import TTSController
from core.timing import TimingManager, time_block
from core.negotiation_engine import NegotiationEngine
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

    # Eager EOT state management
    eager_task = None  # Track speculative LLM generation task
    eager_transcript = None  # Store eager transcript for comparison

    logger.info(f"New WebSocket connection: {session_id}")

    try:
        await websocket.accept()

        # Create session
        session = NegotiationSession(session_id=session_id)
        session_store[session_id] = session

        # Set up components
        deepgram_handler = DeepgramHandler()
        tts = TTSController()
        
        # Create NegotiationEngine for this session
        engine = NegotiationEngine(session)

        async def process_llm_and_tts(text: str, turn_id: str, is_speculative: bool = False):
            """Process LLM generation and stream TTS chunks to client."""
            # Create metrics for this turn
            metrics = timing_manager.create_metrics(
                session_id=session_id,
                turn_id=turn_id,
                transcript_length=len(text),
            )
            metrics.metadata["is_speculative"] = is_speculative

            # Start overall pipeline timing
            metrics.start_event("pipeline_total")

            # Generate LLM response using NegotiationEngine
            async with time_block(metrics, "llm_generation"):
                llm_response = await engine.process_user_message(text)

            # Send Marcus's state to frontend
            await websocket.send_json({
                "type": "marcus_state",
                "patience": session.marcus_state.patience,
                "emotion": session.marcus_state.emotional_state.value,
                "current_offer": session.marcus_state.current_offer,
                "outcome": session.outcome.value if session.outcome else None,
            })

            # Add response length to metadata
            metrics.metadata["response_length"] = len(llm_response)

            # Convert to speech and send
            async with time_block(metrics, "tts_synthesis"):
                audio_bytes = await tts.synthesize(llm_response)

            metrics.metadata["audio_bytes"] = len(audio_bytes)
            
            # Send Marcus's text response to frontend for transcript
            await websocket.send_json({
                "type": "marcus_response",
                "text": llm_response,
            })
            
            await websocket.send_bytes(audio_bytes)

            # End overall timing and log
            metrics.end_event("pipeline_total")
            metrics.log_summary()

            # Cleanup metrics
            timing_manager.cleanup_metrics(session_id, turn_id)

            return llm_response

        async def on_eager_eot(text: str):
            """Handle eager end of turn - start speculative LLM processing."""
            nonlocal eager_task, eager_transcript, turn_counter

            # Cancel any existing eager task
            if eager_task and not eager_task.done():
                eager_task.cancel()
                logger.debug("Cancelled previous eager task")

            # Start speculative processing
            turn_counter += 1
            turn_id = f"turn_{turn_counter}_eager"
            eager_transcript = text

            logger.info(f"Starting speculative processing for: '{text}'")
            eager_task = asyncio.create_task(
                process_llm_and_tts(text, turn_id, is_speculative=True)
            )

        async def on_turn_resumed():
            """Handle turn resumed - cancel speculative work."""
            nonlocal eager_task, eager_transcript

            if eager_task and not eager_task.done():
                eager_task.cancel()
                logger.info("Cancelled speculative processing - user continued speaking")
                try:
                    await eager_task
                except asyncio.CancelledError:
                    pass

            eager_task = None
            eager_transcript = None

        async def on_transcript(text: str, is_final: bool):
            """Handle transcript and generate LLM response if final."""
            nonlocal turn_counter, eager_task, eager_transcript

            # Send transcript to frontend
            await websocket.send_json({
                "type": "transcript",
                "text": text,
                "is_final": is_final,
            })

            # If final transcript, finalize response
            if is_final and text.strip():
                # Check if we have a matching eager task already in progress
                if eager_task and eager_transcript == text:
                    logger.info("Eager task matches final transcript - using speculative result")
                    try:
                        # Wait for the eager task to complete
                        await eager_task
                    except asyncio.CancelledError:
                        # Task was cancelled, process normally
                        logger.info("Eager task was cancelled, processing normally")
                        turn_counter += 1
                        turn_id = f"turn_{turn_counter}"
                        await process_llm_and_tts(text, turn_id, is_speculative=False)
                else:
                    # No matching eager task, process normally
                    if eager_task and not eager_task.done():
                        eager_task.cancel()
                        try:
                            await eager_task
                        except asyncio.CancelledError:
                            pass

                    turn_counter += 1
                    turn_id = f"turn_{turn_counter}"
                    await process_llm_and_tts(text, turn_id, is_speculative=False)

                # Reset eager state
                eager_task = None
                eager_transcript = None

        await deepgram_handler.start_transcription(
            on_transcript=on_transcript,
            on_eager_eot=on_eager_eot,
            on_turn_resumed=on_turn_resumed,
        )

        # Send ready message
        await websocket.send_json({
            "type": "session_init",
            "session_id": session_id,
        })

        # Main loop: receive audio and forward to Deepgram
        while True:
            message = await websocket.receive()

            # Handle disconnect message
            if message.get("type") == "websocket.disconnect":
                logger.info(f"Received disconnect message: {session_id}")
                break

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
        # Cancel any pending eager tasks
        if eager_task and not eager_task.done():
            logger.info("Cancelling pending eager task on cleanup")
            eager_task.cancel()
            try:
                await eager_task
            except asyncio.CancelledError:
                pass

        if deepgram_handler:
            await deepgram_handler.close()
        if session_id in session_store:
            del session_store[session_id]
