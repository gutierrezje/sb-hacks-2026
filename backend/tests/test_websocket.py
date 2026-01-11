"""WebSocket endpoint tests."""

from fastapi.testclient import TestClient
from main import app


def test_websocket_negotiation():
    """Test connecting to the negotiation WebSocket."""
    client = TestClient(app)
    
    with client.websocket_connect("/ws/negotiate") as websocket:
        # 1. Receive session init message
        data = websocket.receive_json()
        assert data["type"] == "session_init"
        assert "session_id" in data
        assert "message" in data
        
        # 2. Send plain text control message
        test_msg = {"type": "control", "action": "test_ping"}
        websocket.send_json(test_msg)
        
        # 3. Send binary audio data (dummy)
        dummy_audio = b"\x00" * 100
        websocket.send_bytes(dummy_audio)
        
        # No crash means success for this basic test
        # In a real scenario, we might assert on the response 
        # but right now the handler just logs it.
