import sys
import os
import pytest
import asyncio
from fastapi.testclient import TestClient

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

def test_websocket_high_frequency_input():
    """
    Test starting multiple interactive tasks and providing inputs rapidly.
    This verifies that the input_manager and WebSocket loop correctly route
    multiple concurrent inputs without collisions or deadlocks.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        num_tasks = 5
        call_ids = []
        
        # 1. Start multiple interactive tasks
        for i in range(num_tasks):
            req_id = f"start_{i}"
            websocket.send_json({
                "type": "start",
                "tool_name": "interactive_task",
                "args": {},
                "request_id": req_id
            })
            
            # Wait for task_started
            found_started = False
            for _ in range(20):
                data = websocket.receive_json()
                if data["type"] == "task_started" and data.get("request_id") == req_id:
                    call_ids.append(data["call_id"])
                    found_started = True
                    break
            assert found_started, f"Failed to start task {i}"

        assert len(call_ids) == num_tasks
        
        # 2. Wait for input requests and spam inputs
        # We'll use a loop to handle the incoming messages
        completed_tasks = set()
        input_provided = set()
        
        # Give some time for all tasks to reach the input request stage
        for _ in range(300):
            data = websocket.receive_json()
            cid = data.get("call_id")
            
            if data["type"] == "input_request":
                # Rapidly send input for this task
                websocket.send_json({
                    "type": "input",
                    "call_id": cid,
                    "value": "yes",
                    "request_id": f"input_{cid}"
                })
                input_provided.add(cid)
            
            if data["type"] == "result":
                completed_tasks.add(cid)
            
            if len(completed_tasks) == num_tasks:
                break
                
        assert len(input_provided) == num_tasks, f"Only {len(input_provided)} tasks requested input"
        assert len(completed_tasks) == num_tasks, f"Only {len(completed_tasks)} tasks completed"
        
        for cid in call_ids:
            assert cid in completed_tasks
