import sys
import os
import pytest
import json
import time
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

client = TestClient(app)

def test_sse_timestamp():
    """Verify that SSE events contain a timestamp."""
    response = client.post(
        "/start_task/long_audit", 
        json={"args": {"duration": 1}}
    )
    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    assert isinstance(data["timestamp"], float)
    
    call_id = data["call_id"]
    
    with client.stream("GET", f"/stream/{call_id}") as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            if line.startswith("data: "):
                event_data = json.loads(line[6:])
                assert "timestamp" in event_data
                assert isinstance(event_data["timestamp"], float)
                # Verify it's a recent timestamp
                assert time.time() - event_data["timestamp"] < 60

def test_websocket_timestamp():
    """Verify that WebSocket messages contain a timestamp."""
    with client.websocket_connect("/ws") as websocket:
        # Test task_started and progress timestamps
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 1},
            "request_id": "req_123"
        })
        
        # task_started
        data = websocket.receive_json()
        assert data["type"] == "task_started"
        assert "timestamp" in data
        assert isinstance(data["timestamp"], float)
        
        # progress/result
        while True:
            data = websocket.receive_json()
            assert "timestamp" in data
            assert isinstance(data["timestamp"], float)
            if data["type"] == "result":
                break

        # Test tools_list timestamp
        websocket.send_json({"type": "list_tools", "request_id": "req_456"})
        data = websocket.receive_json()
        assert data["type"] == "tools_list"
        assert "timestamp" in data
        
        # Test pong timestamp
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        assert data["type"] == "pong"
        assert "timestamp" in data

def test_websocket_stop_and_input_timestamps():
    """Verify that WebSocket stop_success and input_success contain timestamps."""
    with client.websocket_connect("/ws") as websocket:
        # 1. Test stop_success timestamp
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 10},
            "request_id": "req_stop_1"
        })
        
        data = websocket.receive_json() # task_started
        call_id = data["call_id"]
        
        websocket.send_json({
            "type": "stop",
            "call_id": call_id,
            "request_id": "req_stop_2"
        })
        
        # We might get some progress messages before stop_success
        while True:
            data = websocket.receive_json()
            assert "timestamp" in data
            if data["type"] == "stop_success":
                assert data["request_id"] == "req_stop_2"
                break
        
        # 2. Test input_success timestamp
        websocket.send_json({
            "type": "start",
            "tool_name": "interactive_task",
            "request_id": "req_input_1"
        })
        
        data = websocket.receive_json() # task_started
        call_id = data["call_id"]
        
        # Wait for input_request
        while True:
            data = websocket.receive_json()
            assert "timestamp" in data
            if data["type"] == "input_request":
                break
        
        websocket.send_json({
            "type": "input",
            "call_id": call_id,
            "value": "yes",
            "request_id": "req_input_2"
        })
        
        # Wait for input_success
        while True:
            data = websocket.receive_json()
            assert "timestamp" in data
            if data["type"] == "input_success":
                assert data["request_id"] == "req_input_2"
                break

def test_websocket_error_timestamp():
    """Verify that WebSocket error messages contain a timestamp."""
    with client.websocket_connect("/ws") as websocket:
        # Error for unknown tool
        websocket.send_json({
            "type": "start",
            "tool_name": "non_existent_tool",
            "request_id": "req_err_1"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "timestamp" in data
        assert isinstance(data["timestamp"], float)
        assert data["request_id"] == "req_err_1"
        
        # Error for invalid type (missing tool_name)
        websocket.send_json({
            "type": "unknown_type",
            "request_id": "req_err_2"
        })
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "timestamp" in data
        assert "Unknown message type" in data["payload"]["detail"]
