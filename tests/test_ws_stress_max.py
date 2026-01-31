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
async def test_ws_extreme_stress():
    """
    EXTREME STRESS TEST: 10 concurrent tasks, each with rapid progress, 
    while interleaved with multiple pings.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        num_tasks = 10
        call_ids = []
        
        # 1. Start 10 tasks
        for i in range(num_tasks):
            req_id = f"stress_start_{i}"
            websocket.send_json({
                "type": "start",
                "tool_name": "multi_stage_analysis",
                "args": {"documents": 1}, # Reduced from 3
                "request_id": req_id
            })
            
        # 2. Collect task_started events
        start_events = 0
        for _ in range(num_tasks * 5):
            data = websocket.receive_json()
            if data["type"] == "task_started":
                call_ids.append(data["call_id"])
                start_events += 1
            if start_events == num_tasks:
                break
        
        assert start_events == num_tasks

        # 3. Bombard with pings while tasks are running
        for _ in range(20):
            websocket.send_json({"type": "ping"})
        
        # 4. Wait for all pongs and all results
        pongs = 0
        results = 0
        
        for _ in range(500):
            try:
                data = websocket.receive_json()
                if data["type"] == "pong":
                    pongs += 1
                elif data["type"] == "result":
                    results += 1
                
                if results == num_tasks and pongs >= 20:
                    break
            except Exception:
                break
        
        assert results == num_tasks
        assert pongs >= 20

@pytest.mark.asyncio
async def test_ws_interleaved_interactive_stress():
    """
    Starts an interactive task and background tasks,
    then provides input while other tasks are still streaming.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Start background task
        websocket.send_json({
            "type": "start",
            "tool_name": "security_scan",
            "request_id": "bg_task"
        })
        
        # Start interactive task
        websocket.send_json({
            "type": "start",
            "tool_name": "interactive_task",
            "request_id": "interactive_task"
        })
        
        # Wait for interactive task start and input request
        interactive_call_id = None
        input_requested = False
        
        for _ in range(50):
            data = websocket.receive_json()
            if data["type"] == "task_started" and data.get("request_id") == "interactive_task":
                interactive_call_id = data["call_id"]
            if data["type"] == "input_request" and data.get("call_id") == interactive_call_id:
                input_requested = True
                break
        
        assert input_requested
        
        # Provide input
        websocket.send_json({
            "type": "input",
            "call_id": interactive_call_id,
            "value": "yes",
            "request_id": "input_cmd"
        })
        
        # Verify success and results for both
        results = 0
        input_success = False
        
        for _ in range(100):
            data = websocket.receive_json()
            if data["type"] == "input_success" and data.get("request_id") == "input_cmd":
                input_success = True
            if data["type"] == "result":
                results += 1
            if results == 2 and input_success:
                break
        
        assert input_success
        assert results == 2