import sys
import os
import json
import pytest
import asyncio
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

def test_websocket_input_not_waiting():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Start a tool that doesn't request input
        websocket.send_json({
            "type": "start",
            "tool_name": "security_scan",
            "request_id": "req_1"
        })
        
        # Get task_started
        data = websocket.receive_json()
        assert data["type"] == "task_started"
        call_id = data["call_id"]
        
        # Send input immediately (it's not waiting for input)
        websocket.send_json({
            "type": "input",
            "call_id": call_id,
            "value": "unexpected input",
            "request_id": "req_2"
        })
        
        # We should get an error
        data = websocket.receive_json()
        while data.get("type") == "progress":
            data = websocket.receive_json()
            
        assert data["type"] == "error"
        assert data["request_id"] == "req_2"
        assert "No task waiting for input" in data["payload"]["detail"]

def test_websocket_double_stop():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Start a tool
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 10},
            "request_id": "req_1"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "task_started"
        call_id = data["call_id"]
        
        # Stop it
        websocket.send_json({
            "type": "stop",
            "call_id": call_id,
            "request_id": "req_2"
        })
        
        # Wait for stop_success (might get some progress first)
        data = websocket.receive_json()
        while data.get("type") == "progress":
            data = websocket.receive_json()
        
        assert data["type"] == "stop_success"
        
        # Stop it again
        websocket.send_json({
            "type": "stop",
            "call_id": call_id,
            "request_id": "req_3"
        })
        
        # Should get error
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data["request_id"] == "req_3"
        assert "No active task found" in data["payload"]["detail"]

def test_websocket_start_invalid_args():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # long_audit expects 'duration' as int
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": "not an int"},
            "request_id": "req_invalid_args"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data["request_id"] == "req_invalid_args"
        # FastAPI/Pydantic validation error or tool initialization error
        assert "payload" in data

def test_websocket_dynamic_echo():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "type": "start",
            "tool_name": "dynamic_echo_tool",
            "args": {"message": "Test Echo", "repeat": 2},
            "request_id": "req_echo"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "task_started"
        
        # Receive progress
        p1 = websocket.receive_json()
        assert p1["type"] == "progress"
        assert p1["payload"]["step"] == "Echoing 1/2"
        assert p1["payload"]["log"] == "Message: Test Echo"
        
        p2 = websocket.receive_json()
        assert p2["type"] == "progress"
        assert p2["payload"]["step"] == "Echoing 2/2"
        
        # Receive result
        res = websocket.receive_json()
        assert res["type"] == "result"
        assert res["payload"]["echoed"] == "Test Echo"
        assert res["payload"]["count"] == 2