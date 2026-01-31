import sys
import os
import json
import pytest
import asyncio
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

def test_websocket_invalid_json():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Send raw invalid JSON
        websocket.send_text("not a json")
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "Invalid JSON" in data["payload"]["detail"]

def test_websocket_non_dict_json():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Send a JSON list instead of a dict
        websocket.send_json([1, 2, 3])
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "Message must be a JSON object" in data["payload"]["detail"]

def test_websocket_unknown_type():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({"type": "unknown_command"})
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "Unknown message type" in data["payload"]["detail"]

def test_websocket_missing_tool():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "type": "start",
            "tool_name": "missing_tool",
            "request_id": "robust_1"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data["request_id"] == "robust_1"
        assert "Tool not found" in data["payload"]["detail"]

def test_websocket_ping_pong():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({"type": "ping"})
        
        data = websocket.receive_json()
        assert data["type"] == "pong"

def test_websocket_unknown_type_with_request_id():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "type": "unknown_command",
            "request_id": "robust_unknown"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data.get("request_id") == "robust_unknown"
        assert "Unknown message type" in data["payload"]["detail"]

def test_websocket_message_size_limit():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Create a message larger than 1MB (default limit)
        large_payload = "a" * (1024 * 1024 + 100)
        large_message = json.dumps({"type": "ping", "data": large_payload})
        
        websocket.send_text(large_message)
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "Message too large" in data["payload"]["detail"]

def test_websocket_start_missing_tool_name():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "type": "start",
            "request_id": "missing_tool_name"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data["request_id"] == "missing_tool_name"
        assert "Tool not found" in data["payload"]["detail"]

def test_websocket_stop_missing_call_id():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "type": "stop",
            "request_id": "missing_call_id"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data["request_id"] == "missing_call_id"
        assert "No active task found" in data["payload"]["detail"]

def test_websocket_input_missing_call_id():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "type": "input",
            "value": "some value",
            "request_id": "input_missing_call_id"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data["request_id"] == "input_missing_call_id"
        assert "No task waiting for input" in data["payload"]["detail"]

def test_websocket_input_missing_value():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "type": "input",
            "call_id": "some_id",
            "request_id": "input_missing_value"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data["request_id"] == "input_missing_value"
        assert "No task waiting for input" in data["payload"]["detail"]

def test_websocket_message_size_limit_and_recover():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Send large message
        large_payload = "a" * (1024 * 1024 + 100)
        websocket.send_text(json.dumps({"type": "ping", "data": large_payload}))
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "Message too large" in data["payload"]["detail"]
        
        # 2. Send normal message to verify recovery
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        assert data["type"] == "pong"