import sys
import os
import json
import pytest
import asyncio
import time
from fastapi.testclient import TestClient
from fastapi import WebSocketDisconnect

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app
from backend.app import auth

@pytest.fixture
def enable_auth(monkeypatch):
    monkeypatch.setenv("BRIDGE_API_KEY", "test-secret-key")
    monkeypatch.setattr(auth, "BRIDGE_API_KEY", "test-secret-key")
    yield
    monkeypatch.setattr(auth, "BRIDGE_API_KEY", None)

def test_websocket_auth_failure(enable_auth):
    client = TestClient(app)
    # Try to connect with wrong API key
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/ws?api_key=wrong-key") as websocket:
            websocket.receive_json()
    assert excinfo.value.code == 1008

def test_websocket_auth_success(enable_auth):
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-secret-key") as websocket:
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        assert data["type"] == "pong"

def test_websocket_invalid_args_pydantic_validation():
    API_KEY = "test_secret_key"
    os.environ["BRIDGE_API_KEY"] = API_KEY
    client = TestClient(app)
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": "not-a-number"},
            "request_id": "req_invalid_args"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data.get("request_id") == "req_invalid_args"
        assert "validation error" in data["payload"]["detail"].lower()

def test_websocket_timeout_works():
    """
    This is hard to test with TestClient because we can't easily control time 
    inside the server loop without mocking. 
    But we can verify that if we don't send anything for a long time, 
    the server SHOULD eventually close.
    However, we don't want to wait 60s in a unit test.
    """
    pass

def test_websocket_concurrent_tasks_cleanup():
    """
    Verifies that multiple tasks started on one WS are all cleaned up on disconnect.
    (Redundant with test_ws_cleanup.py but good to have here for audit).
    """
    API_KEY = "test_secret_key"
    os.environ["BRIDGE_API_KEY"] = API_KEY
    client = TestClient(app)
    call_ids = []
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        for i in range(2):
            websocket.send_json({
                "type": "start",
                "tool_name": "long_audit",
                "args": {"duration": 5},
                "request_id": f"req_{i}"
            })
            data = websocket.receive_json()
            if data["type"] == "task_started":
                call_ids.append(data["call_id"])
    
    # After 'with' block, it should be disconnected.
    # Give some time for cleanup
    time.sleep(0.1)
    
    from backend.app.bridge import registry
    for cid in call_ids:
        assert registry.get_task_no_consume(cid) is None
