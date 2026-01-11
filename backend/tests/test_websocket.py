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

        # 2. Send end_session to cleanly close
        websocket.send_json({"type": "end_session"})
