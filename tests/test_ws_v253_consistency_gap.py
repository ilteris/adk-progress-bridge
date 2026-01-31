import pytest
import asyncio
import json
import time
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.bridge import PROTOCOL_VERSION

def test_ws_v253_stop_consistency():
    """
    Check if 'protocol_version' is present in the progress update sent during a stop command.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        # 1. Start a long-running task
        websocket.send_json({"type": "start", "tool_name": "long_audit", "request_id": "req-1"})
        data = websocket.receive_json()
        assert data["type"] == "task_started"
        call_id = data["call_id"]
        
        # 2. Immediately stop it
        websocket.send_json({"type": "stop", "call_id": call_id, "request_id": "req-2"})
        
        # 3. We should receive a progress event with "Cancelled"
        # and then a "stop_success" event.
        
        found_cancelled = False
        found_stop_success = False
        
        for _ in range(10): # try a few times
            data = websocket.receive_json()
            if data["type"] == "progress" and data["payload"].get("step") == "Cancelled":
                found_cancelled = True
                print(f"DEBUG: Cancelled event: {data}")
                assert "protocol_version" in data, "protocol_version missing in progress update during stop"
                assert data["protocol_version"] == PROTOCOL_VERSION
            if data["type"] == "stop_success":
                found_stop_success = True
                assert "protocol_version" in data
                break
        
        assert found_cancelled
        assert found_stop_success
