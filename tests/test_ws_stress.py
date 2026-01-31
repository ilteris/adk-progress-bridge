import pytest
import asyncio
import json
import uuid
import sys
import os
import time

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.mark.asyncio
async def test_ws_concurrency_stress():
    """
    Stress test to ensure the WebSocket send_lock handles many concurrent tasks sending messages.
    """
    from backend.app.main import run_ws_generator
    from backend.app.bridge import ProgressPayload
    
    mock_messages = []
    async def mock_send(data):
        mock_messages.append(data)
        await asyncio.sleep(0.001) # Small delay

    # Simulate a tool that yields many progress updates
    async def fast_tool():
        for i in range(100):
            yield ProgressPayload(step="Stress", pct=i, log=f"Update {i}")

    # Run many concurrent generators
    tasks = []
    active_tasks = {}
    for i in range(20): # Increased to 20
        call_id = str(uuid.uuid4())
        tasks.append(run_ws_generator(mock_send, call_id, "fast_tool", fast_tool(), active_tasks))

    await asyncio.gather(*tasks)
    
    # 20 tasks * 100 updates each = 2000 messages
    assert len(mock_messages) >= 2000
    print(f"Stress test passed with {len(mock_messages)} messages")

def test_ws_ping_pong():
    """Test the WebSocket heartbeat ping/pong mechanism."""
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        assert data["type"] == "pong"

def test_ws_rapid_commands():
    """
    Test sending rapid 'stop' and 'start' commands to ensure no race conditions.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Rapidly start and stop multiple tasks
        call_ids = []
        for i in range(5):
            req_id = f"start-{i}"
            websocket.send_json({
                "type": "start",
                "tool_name": "long_audit",
                "args": {"duration": 1},
                "request_id": req_id
            })
            
            # Wait for task_started
            found_start = False
            while not found_start:
                data = websocket.receive_json()
                if data["type"] == "task_started" and data.get("request_id") == req_id:
                    call_ids.append(data["call_id"])
                    found_start = True

        # Rapidly stop them all
        for i, call_id in enumerate(call_ids):
            req_id = f"stop-{i}"
            websocket.send_json({
                "type": "stop",
                "call_id": call_id,
                "request_id": req_id
            })
            
        # Verify we get stop_success for all
        stops_found = 0
        timeout = 5.0
        start_time = time.time()
        while stops_found < 5:
            if time.time() - start_time > timeout:
                pytest.fail("Timed out waiting for stop_success")
            data = websocket.receive_json()
            if data["type"] == "stop_success":
                stops_found += 1
        
        assert stops_found == 5