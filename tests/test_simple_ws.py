from fastapi.testclient import TestClient
from backend.app.main import app

def test_simple_ping():
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "connected"
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        assert data["type"] == "pong"
