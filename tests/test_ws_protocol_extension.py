import sys
import os
import json
import pytest
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

@pytest.mark.asyncio
async def test_websocket_list_tools():
    """
    Tests that listing tools over WebSocket works.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        req_id = "list_req_1"
        websocket.send_json({
            "type": "list_tools",
            "request_id": req_id
        })
        
        data = websocket.receive_json()
        assert data["type"] == "tools_list"
        assert isinstance(data["tools"], list)
        assert len(data["tools"]) > 0
        assert "long_audit" in data["tools"]
        assert data["request_id"] == req_id

@pytest.mark.asyncio
async def test_rest_list_tools():
    """
    Tests that listing tools over REST works.
    """
    client = TestClient(app)
    response = client.get("/tools")
    assert response.status_code == 200
    tools = response.json()
    assert isinstance(tools, list)
    assert "long_audit" in tools

@pytest.mark.asyncio
async def test_websocket_stop_acknowledgement():
    """
    Tests that stopping a task over WebSocket returns a stop_success acknowledgement.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Start a task
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 10},
            "request_id": "start_1"
        })
        
        start_data = websocket.receive_json()
        call_id = start_data["call_id"]
        
        # Receive first progress event
        websocket.receive_json()
        
        # Send stop
        req_id = "stop_req_1"
        websocket.send_json({
            "type": "stop",
            "call_id": call_id,
            "request_id": req_id
        })
        
        # Should receive progress (Cancelled) AND stop_success
        messages = []
        for _ in range(2):
            messages.append(websocket.receive_json())
            
        types = [m["type"] for m in messages]
        assert "progress" in types
        assert "stop_success" in types
        
        stop_success = next(m for m in messages if m["type"] == "stop_success")
        assert stop_success["call_id"] == call_id
        assert stop_success["request_id"] == req_id

@pytest.mark.asyncio
async def test_websocket_input_acknowledgement():
    """
    Tests that providing input over WebSocket returns an input_success acknowledgement.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Start interactive task
        websocket.send_json({
            "type": "start",
            "tool_name": "interactive_task",
            "args": {},
            "request_id": "start_2"
        })
        
        start_data = websocket.receive_json()
        call_id = start_data["call_id"]
        
        # Receive first progress event
        progress = websocket.receive_json()
        assert progress["type"] == "progress"

        # Receive input_request
        input_request = websocket.receive_json()
        assert input_request["type"] == "input_request"
        
        # Send input
        req_id = "input_req_1"
        websocket.send_json({
            "type": "input",
            "call_id": call_id,
            "value": "yes",
            "request_id": req_id
        })
        
        # Should receive input_success
        data = websocket.receive_json()
        assert data["type"] == "input_success"
        assert data["call_id"] == call_id
        assert data["request_id"] == req_id