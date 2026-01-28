import sys
import os
import json
import pytest
import asyncio
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

@pytest.mark.asyncio
async def test_websocket_ping_pong():
    """
    Tests that the WebSocket endpoint responds to ping with pong.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        assert data["type"] == "pong"

@pytest.mark.asyncio
async def test_websocket_concurrency():
    """
    Tests that multiple tasks can run concurrently over the same WebSocket connection.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Start 3 tasks
        call_ids = []
        for i in range(3):
            req_id = f"concurrency_req_{i}"
            websocket.send_json({
                "type": "start",
                "tool_name": "long_audit",
                "args": {"duration": 1},
                "request_id": req_id
            })
            
            # We get task_started, but might receive progress from previous tasks first
            found_started = False
            for _ in range(20):
                data = websocket.receive_json()
                if data["type"] == "task_started" and data.get("request_id") == req_id:
                    call_ids.append(data["call_id"])
                    found_started = True
                    break
            assert found_started, f"Should have received task_started for {req_id}"
        
        assert len(set(call_ids)) == 3, "Should have 3 unique call IDs"
        
        # Now we expect to receive a mix of events for all 3 call IDs
        results_received = set()
        for _ in range(100):
            try:
                data = websocket.receive_json()
                if data["type"] == "result":
                    results_received.add(data["call_id"])
                
                if len(results_received) == 3:
                    break
            except Exception:
                break
        
        assert results_received == set(call_ids), f"Should have received results for all tasks. Got: {results_received}"

@pytest.mark.asyncio
async def test_websocket_concurrent_input():
    """
    Tests that multiple tasks can wait for and receive input concurrently.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Start 2 interactive tasks
        call_ids = []
        for i in range(2):
            req_id = f"input_req_{i}"
            websocket.send_json({
                "type": "start",
                "tool_name": "interactive_task",
                "args": {},
                "request_id": req_id
            })
            
            found_started = False
            for _ in range(10):
                data = websocket.receive_json()
                if data["type"] == "task_started" and data.get("request_id") == req_id:
                    call_ids.append(data["call_id"])
                    found_started = True
                    break
            assert found_started, f"Should have received task_started for {req_id}"
        
        waiting_for_ids = set()
        results_received = set()
        
        # Loop until both are finished
        for _ in range(100):
            data = websocket.receive_json()
            cid = data.get("call_id")
            
            if data["type"] == "input_request":
                waiting_for_ids.add(cid)
                # Send input for this specific CID
                websocket.send_json({
                    "type": "input",
                    "call_id": cid,
                    "value": "yes"
                })
            
            if data["type"] == "result":
                results_received.add(cid)
            
            if len(results_received) == 2:
                break
        
        assert len(waiting_for_ids) == 2, "Both tasks should have requested input"
        assert len(results_received) == 2, "Both tasks should have completed"