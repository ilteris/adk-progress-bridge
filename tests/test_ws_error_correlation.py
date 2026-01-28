import sys
import os
import json
import pytest
from fastapi.testclient import TestClient

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set API key for tests before importing app
API_KEY = "test_secret_key"
os.environ["BRIDGE_API_KEY"] = API_KEY

from backend.app.main import app

@pytest.mark.asyncio
async def test_websocket_start_error_correlation():
    """
    Tests that an error starting a task over WebSocket includes the request_id.
    """
    client = TestClient(app)
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        req_id = "error_test_req_123"
        websocket.send_json({
            "type": "start",
            "tool_name": "non_existent_tool",
            "args": {},
            "request_id": req_id
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data.get("request_id") == req_id
        assert "Tool not found" in data["payload"]["detail"]

@pytest.mark.asyncio
async def test_websocket_malformed_json():
    """
    Tests that the WebSocket endpoint doesn't crash on malformed JSON.
    """
    client = TestClient(app)
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        # Send invalid JSON
        websocket.send_text("not a json")
        
        # We now send an error message back for malformed JSON
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "Invalid JSON" in data["payload"]["detail"]

@pytest.mark.asyncio
async def test_websocket_stop_error_correlation():
    """
    Tests that an error stopping a non-existent task includes the request_id and call_id.
    """
    client = TestClient(app)
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        req_id = "stop_error_req_456"
        c_id = "non_existent_call_id"
        websocket.send_json({
            "type": "stop",
            "call_id": c_id,
            "request_id": req_id
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data.get("request_id") == req_id
        assert data.get("call_id") == c_id
        # The message is "No active task found..."
        assert "found" in data["payload"]["detail"].lower()
        assert "active task" in data["payload"]["detail"].lower()

@pytest.mark.asyncio
async def test_websocket_input_error_correlation():
    """
    Tests that an error providing input for a non-existent task includes the request_id and call_id.
    """
    client = TestClient(app)
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        req_id = "input_error_req_789"
        c_id = "non_existent_call_id"
        websocket.send_json({
            "type": "input",
            "call_id": c_id,
            "value": "some value",
            "request_id": req_id
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data.get("request_id") == req_id
        assert data.get("call_id") == c_id
        # The message is "No task waiting for input..."
        assert "waiting for input" in data["payload"]["detail"].lower()