import sys
import os
import json
import pytest
import asyncio
from fastapi.testclient import TestClient

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app, WS_MESSAGE_SIZE_LIMIT

@pytest.mark.asyncio
async def test_websocket_message_size_limit_v157():
    """
    Verifies that messages exceeding the WS_MESSAGE_SIZE_LIMIT are rejected.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        # Create a large payload (slightly over the limit)
        large_payload = "x" * (WS_MESSAGE_SIZE_LIMIT + 100)
        
        websocket.send_text(json.dumps({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"log_data": large_payload},
            "request_id": "large_req_v157"
        }))
        
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "Message too large" in data["payload"]["detail"]
        # request_id is not included in this specific error path yet (in the loop before parsing)
        # Wait, if it fails before parsing it won't have request_id.

@pytest.mark.asyncio
async def test_websocket_stress_concurrency_v157():
    """
    Starts 10 tasks concurrently and verifies they all finish.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        num_tasks = 10
        call_ids = []
        
        # 1. Start 10 tasks
        for i in range(num_tasks):
            req_id = f"stress_v157_{i}"
            websocket.send_json({
                "type": "start",
                "tool_name": "long_audit",
                "args": {"duration": 1},
                "request_id": req_id
            })
            
        # 2. Collect task_started
        for _ in range(num_tasks * 2):
            data = websocket.receive_json()
            if data["type"] == "task_started":
                call_ids.append(data["call_id"])
            if len(call_ids) == num_tasks:
                break
        
        assert len(call_ids) == num_tasks
        
        # 3. Collect results
        results = set()
        for _ in range(300):
            data = websocket.receive_json()
            if data["type"] == "result":
                results.add(data["call_id"])
            if len(results) == num_tasks:
                break
                
        assert len(results) == num_tasks

@pytest.mark.asyncio
async def test_websocket_rapid_ping_pong_v157():
    """
    Sends 50 pings rapidly and verifies 50 pongs.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        for i in range(50):
            websocket.send_json({"type": "ping"})
            
        pongs = 0
        for i in range(100):
            data = websocket.receive_json()
            if data["type"] == "pong":
                pongs += 1
            if pongs == 50:
                break
        assert pongs == 50
