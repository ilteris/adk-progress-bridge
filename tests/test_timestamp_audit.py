import sys
import os
import json
import pytest
import time
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

def test_websocket_timestamp():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Start a task
        start_time = time.time()
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 1},
            "request_id": "test_req_ts"
        })
        
        # 2. Receive task_started
        data = websocket.receive_json()
        assert "timestamp" in data
        assert data["timestamp"] >= start_time
        
        # 3. Receive progress
        data = websocket.receive_json()
        assert "timestamp" in data
        assert data["timestamp"] >= start_time

def test_websocket_stop_and_input_timestamps():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Start interactive task
        websocket.send_json({
            "type": "start",
            "tool_name": "interactive_task",
            "args": {},
            "request_id": "req_1"
        })
        
        websocket.receive_json() # task_started
        websocket.receive_json() # progress
        data = websocket.receive_json() # input_request
        assert "timestamp" in data
        call_id = data["call_id"]
        
        # 2. Test input_success timestamp
        now = time.time()
        websocket.send_json({
            "type": "input",
            "call_id": call_id,
            "value": "yes",
            "request_id": "input_req"
        })
        data = websocket.receive_json()
        assert data["type"] == "input_success"
        assert "timestamp" in data
        assert data["timestamp"] >= now
        
        # 3. Test stop_success timestamp (we'll start another task for this)
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 5},
            "request_id": "req_2"
        })
        data = websocket.receive_json()
        new_call_id = data["call_id"]
        
        now = time.time()
        websocket.send_json({
            "type": "stop",
            "call_id": new_call_id,
            "request_id": "stop_req"
        })
        
        found_stop_success = False
        for _ in range(5):
            data = websocket.receive_json()
            if data["type"] == "stop_success":
                found_stop_success = True
                assert "timestamp" in data
                assert data["timestamp"] >= now
                break
        assert found_stop_success

def test_websocket_error_timestamp():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        now = time.time()
        websocket.send_json({
            "type": "start",
            "tool_name": "non_existent",
            "request_id": "error_req"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "timestamp" in data
        assert data["timestamp"] >= now
