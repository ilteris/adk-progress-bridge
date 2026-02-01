import sys
import os
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from fastapi import status

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app
from backend.app import auth

@pytest.fixture
def enable_auth(monkeypatch):
    monkeypatch.setenv("BRIDGE_API_KEY", "test-secret-key")
    # We need to reload the BRIDGE_API_KEY in the auth module because it's evaluated at import time
    monkeypatch.setattr(auth, "BRIDGE_API_KEY", "test-secret-key")
    yield
    monkeypatch.setattr(auth, "BRIDGE_API_KEY", None)

def test_websocket_auth_disabled_by_default():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        assert data["type"] == "pong"

def test_websocket_auth_enabled_no_key(enable_auth):
    client = TestClient(app)
    # When auth is enabled, connecting without a key should fail after accept
    with client.websocket_connect("/ws") as websocket:
        with pytest.raises(WebSocketDisconnect) as exc:
            websocket.receive_json()
        assert exc.value.code == status.WS_1008_POLICY_VIOLATION

def test_websocket_auth_enabled_wrong_key(enable_auth):
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=wrong") as websocket:
        with pytest.raises(WebSocketDisconnect) as exc:
            websocket.receive_json()
        assert exc.value.code == status.WS_1008_POLICY_VIOLATION

def test_websocket_auth_enabled_correct_key(enable_auth):
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-secret-key") as websocket:
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        assert data["type"] == "pong"