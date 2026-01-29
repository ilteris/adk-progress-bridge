import sys
import os
import json
import pytest
import asyncio
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set API key for tests before importing app
API_KEY = "test_secret_key"
os.environ["BRIDGE_API_KEY"] = API_KEY

from backend.app.main import app

def test_call_id_collision():
    client = TestClient(app)
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        # 1. Start a task with a specific call_id
        shared_call_id = "shared_id_123"
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 1},
            "call_id": shared_call_id,
            "request_id": "req_1"
        })
        
        # 2. Start another task with the SAME call_id
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 1},
            "call_id": shared_call_id,
            "request_id": "req_2"
        })
        
        found_success = False
        found_collision_error = False
        
        for _ in range(20):
            data = websocket.receive_json()
            if data.get("request_id") == "req_1" and data["type"] == "task_started":
                found_success = True
            if data.get("request_id") == "req_2" and data["type"] == "error":
                if "already exists" in data["payload"]["detail"]:
                    found_collision_error = True
            
            if found_success and found_collision_error:
                break
        
        assert found_success
        assert found_collision_error

if __name__ == "__main__":
    test_call_id_collision()
