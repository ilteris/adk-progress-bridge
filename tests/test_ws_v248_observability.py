import sys
import os
import json
import pytest
import time
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app, PROTOCOL_VERSION

def test_v248_observability_and_protocol():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Test protocol version and timestamp in list_tools
        websocket.send_json({
            "type": "list_tools",
            "request_id": "req_v248_list"
        })
        data = websocket.receive_json()
        assert data["type"] == "tools_list"
        assert data["protocol_version"] == PROTOCOL_VERSION
        assert data["protocol_version"] == "1.1.0"
        assert "timestamp" in data
        
        # 2. Test timestamp and protocol version in task_started
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 1},
            "request_id": "req_v248_start"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "task_started"
        assert data["protocol_version"] == PROTOCOL_VERSION
        assert "timestamp" in data
        
        # 3. Test timestamp in progress events
        found_progress = False
        start_time = time.time()
        for _ in range(10):
            data = websocket.receive_json()
            if data["type"] == "progress":
                found_progress = True
                assert "timestamp" in data
                assert isinstance(data["timestamp"], (int, float))
                # Timestamp should be recent
                assert abs(data["timestamp"] - start_time) < 10
                break
        assert found_progress

def test_v248_rest_protocol_header():
    client = TestClient(app)
    response = client.get("/tools")
    assert response.status_code == 200
    assert response.headers["X-Protocol-Version"] == PROTOCOL_VERSION