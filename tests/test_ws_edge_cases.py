import sys
import os
import json
import pytest
import asyncio
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

def test_websocket_missing_fields_start():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Missing tool_name
        websocket.send_json({
            "type": "start",
            "request_id": "missing_1"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data["request_id"] == "missing_1"
        assert "Tool not found" in data["payload"]["detail"]

def test_websocket_missing_fields_stop():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Missing call_id
        websocket.send_json({
            "type": "stop",
            "request_id": "missing_2"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data["request_id"] == "missing_2"
        assert "No active task found" in data["payload"]["detail"]

def test_websocket_missing_fields_input():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Missing call_id
        websocket.send_json({
            "type": "input",
            "request_id": "missing_3",
            "value": "something"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data["request_id"] == "missing_3"
        assert "No task waiting for input" in data["payload"]["detail"]

def test_websocket_start_and_immediate_disconnect():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 1},
            "request_id": "disconnect_test"
        })
        # Wait for acknowledgment
        data = websocket.receive_json()
        assert data["type"] == "task_started"
        # Disconnect immediately
        websocket.close()
    
    # No crash should happen, background task should cleanup.