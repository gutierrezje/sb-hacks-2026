"""WebSocket endpoint for salary negotiation sessions."""

import logging
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from models.session import NegotiationSession
from store.sessions import session_store


logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/negotiate")
async def negotiate_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time salary negotiation.
    
    This endpoint handles:
    - Connection lifecycle management
    - Session creation and binding
    - Binary audio data (from client microphone)
    - JSON control messages (state updates, events)
    - Bidirectional communication with client
    
    Message Protocol:
        Client -> Server:
            - Binary: PCM audio chunks (16-bit, 16kHz, mono)
            - JSON: {"type": "control", "action": "..."}
        
        Server -> Client:
            - Binary: TTS audio chunks
            - JSON: {"type": "transcript|state|event", "data": {...}}
    """
    session_id = str(uuid4())
    
    logger.info(f"New WebSocket connection attempt: {session_id}")
    
    try:
        # Accept the WebSocket connection
        await websocket.accept()
        logger.info(f"WebSocket accepted: {session_id}")
        
        # Create new negotiation session
        session = NegotiationSession(session_id=session_id)
        session_store[session_id] = session
        
        logger.info(f"Session created: {session_id}")
        
        # Send session initialization message
        await websocket.send_json({
            "type": "session_init",
            "session_id": session_id,
            "message": "Connected to Salary Dojo. Ready to negotiate.",
        })
        
        # Main message loop
        while True:
            # Receive message (can be binary or text)
            message = await websocket.receive()
            
            if "bytes" in message:
                # Binary audio data from client
                audio_data = message["bytes"]
                logger.debug(f"Received audio chunk: {len(audio_data)} bytes")
                
                # TODO: Process audio through STT pipeline
                # await audio_pipeline.process_audio(audio_data)
                
            elif "text" in message:
                # JSON control message
                import json
                data = json.loads(message["text"])
                logger.debug(f"Received control message: {data.get('type')}")
                
                # TODO: Handle control messages
                # - start_recording
                # - stop_recording
                # - end_session
                
            else:
                logger.warning(f"Unknown message type received: {message}")
    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {session_id}")
    
    except Exception as e:
        logger.error(f"Error in WebSocket handler: {e}", exc_info=True)
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass
    
    finally:
        # Cleanup session
        if session_id in session_store:
            logger.info(f"Cleaning up session: {session_id}")
            del session_store[session_id]
