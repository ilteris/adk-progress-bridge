import sys
import os
import json
import pytest
import time
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app
from backend.app.bridge import PROTOCOL_VERSION

def test_v249_comprehensive_protocol_and_timestamps():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Start a task
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 1},
            "request_id": "req_v249_start"
        })
        
        # 2. Check task_started event
        data = websocket.receive_json()
        assert data["type"] == "task_started"
        assert data["protocol_version"] == PROTOCOL_VERSION
        assert "timestamp" in data
        
        # 3. Check progress events for protocol_version
        found_progress = False
        for _ in range(20):
            data = websocket.receive_json()
            if data["type"] == "progress":
                found_progress = True
                assert data["protocol_version"] == PROTOCOL_VERSION
                assert "timestamp" in data
            if data["type"] == "result":
                assert data["protocol_version"] == PROTOCOL_VERSION
                assert "timestamp" in data
                break
        assert found_progress

def test_v249_sse_observability():
    client = TestClient(app)
    # Start task via REST
    resp = client.post("/start_task/long_audit", json={"args": {"duration": 1}})
    assert resp.status_code == 200, f"Response: {resp.text}"
    call_id = resp.json()["call_id"]
    
    # Stream via SSE
    with client.stream("GET", f"/stream/{call_id}") as response:
        for line in response.iter_lines():
            if line.startswith("data: "):
                data = json.loads(line[6:])
                assert "protocol_version" in data
                assert data["protocol_version"] == PROTOCOL_VERSION
                assert "timestamp" in data
                if data["type"] == "result":
                    break