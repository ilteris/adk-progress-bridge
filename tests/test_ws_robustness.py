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

def test_websocket_invalid_json():
    client = TestClient(app)
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        # Send raw invalid JSON
        websocket.send_text("not a json")
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "Invalid JSON" in data["payload"]["detail"]

def test_websocket_non_dict_json():
    client = TestClient(app)
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        # Send a JSON list instead of a dict
        websocket.send_json([1, 2, 3])
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "must be a JSON object" in data["payload"]["detail"]

def test_websocket_unknown_type():
    client = TestClient(app)
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        websocket.send_json({"type": "unknown_command"})
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "Unknown message type" in data["payload"]["detail"]

def test_websocket_missing_tool():
    client = TestClient(app)
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        websocket.send_json({
            "type": "start",
            "tool_name": "missing_tool",
            "request_id": "robust_1"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data.get("request_id") == "robust_1"
        assert "Tool not found" in data["payload"]["detail"]

def test_websocket_ping_pong():
    client = TestClient(app)
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        websocket.send_json({"type": "ping"})
        
        data = websocket.receive_json()
        assert data["type"] == "pong"

def test_websocket_unknown_type_with_request_id():
    client = TestClient(app)
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        websocket.send_json({
            "type": "unknown_command",
            "request_id": "robust_unknown"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data.get("request_id") == "robust_unknown"
        assert "Unknown message type" in data["payload"]["detail"]