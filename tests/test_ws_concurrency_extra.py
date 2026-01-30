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

@pytest.mark.asyncio
async def test_websocket_concurrent_tasks_stress():
    """
    Stress test to ensure the thread-safe send lock handles many concurrent tasks
    streaming events to the same WebSocket connection.
    """
    client = TestClient(app)
    # TestClient.websocket_connect is not async, so we use it in a with block
    # but we can simulate multiple tasks by starting them one after another
    # and then listening for all their events.
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        num_tasks = 10
        request_ids = [f"req_{i}" for i in range(num_tasks)]
        
        # Start many tasks
        for req_id in request_ids:
            websocket.send_json({
                "type": "start",
                "tool_name": "long_audit",
                "args": {"duration": 1},
                "request_id": req_id
            })
        
        # We expect task_started for each, plus many progress events, plus result for each
        # Total events: num_tasks * (1 started + ~5 progress + 1 result) = ~70 events
        events_received = 0
        results_received = 0
        task_started_received = 0
        
        # Use a timeout-like mechanism with range
        for _ in range(200):
            try:
                data = websocket.receive_json()
                events_received += 1
                if data["type"] == "task_started":
                    task_started_received += 1
                elif data["type"] == "result":
                    results_received += 1
                
                if results_received == num_tasks:
                    break
            except Exception:
                break
        
        assert task_started_received == num_tasks
        assert results_received == num_tasks
        print(f"Successfully received {events_received} events from {num_tasks} concurrent tasks.")

def test_websocket_malformed_messages_robustness():
    """
    Send various malformed messages and ensure the server doesn't crash and responds gracefully.
    """
    client = TestClient(app)
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        # 1. Missing type
        websocket.send_json({"request_id": "missing_type"})
        data = websocket.receive_json()
        assert data["type"] == "error"
        
        # 2. Unknown type
        websocket.send_json({"type": "unknown_action", "request_id": "unknown_type"})
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data.get("request_id") == "unknown_type"
        
        # 3. Invalid types for fields
        websocket.send_json({"type": "start", "tool_name": 123, "request_id": "invalid_field_type"})
        data = websocket.receive_json()
        assert data["type"] == "error"
        
        # 4. Empty message
        websocket.send_json({})
        data = websocket.receive_json()
        assert data["type"] == "error"
