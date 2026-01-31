import pytest
import asyncio
import json
import time
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.bridge import PROTOCOL_VERSION

def test_ws_v250_supreme_consistency():
    """
    ULTIMATE PROTOCOL CONSISTENCY CHECK:
    Every single WebSocket response must carry protocol_version and timestamp.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        # 1. Check list_tools
        websocket.send_json({"type": "list_tools", "request_id": "req-1"})
        data = websocket.receive_json()
        assert data["type"] == "tools_list"
        assert data["protocol_version"] == PROTOCOL_VERSION
        assert "timestamp" in data
        
        # 2. Check ping/pong
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        assert data["type"] == "pong"
        # Let's see if pong has them
        assert data["protocol_version"] == PROTOCOL_VERSION
        assert "timestamp" in data

        # 3. Check start
        websocket.send_json({"type": "start", "tool_name": "long_audit", "request_id": "req-2"})
        data = websocket.receive_json()
        assert data["type"] == "task_started"
        assert data["protocol_version"] == PROTOCOL_VERSION
        assert "timestamp" in data
        call_id = data["call_id"]
        
        # 4. Check progress (via ProgressEvent)
        data = websocket.receive_json()
        assert data["type"] == "progress"
        assert data["protocol_version"] == PROTOCOL_VERSION
        assert "timestamp" in data
        
        # 5. Check stop_success
        websocket.send_json({"type": "stop", "call_id": call_id, "request_id": "req-3"})
        # We might get more progress events before stop_success
        while True:
            data = websocket.receive_json()
            if data["type"] == "stop_success":
                break
        
        assert data["protocol_version"] == PROTOCOL_VERSION
        assert "timestamp" in data

        # 6. Check error response for invalid tool
        websocket.send_json({"type": "start", "tool_name": "non_existent", "request_id": "req-4"})
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data["protocol_version"] == PROTOCOL_VERSION
        assert "timestamp" in data

        # 7. Check error response for unknown message type
        websocket.send_json({"type": "unknown_type", "request_id": "req-5"})
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data["protocol_version"] == PROTOCOL_VERSION
        assert "timestamp" in data
