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
