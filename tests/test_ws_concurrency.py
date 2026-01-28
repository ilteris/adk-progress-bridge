import sys
import os
import json
import pytest
import asyncio
from fastapi.testclient import TestClient

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set API key for tests before importing app
API_KEY = "test_secret_key"
os.environ["BRIDGE_API_KEY"] = API_KEY

from backend.app.main import app

def test_websocket_ping_pong():
    """
    Tests that the WebSocket endpoint responds to ping with pong.
    """
    client = TestClient(app)
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        assert data["type"] == "pong"

def test_websocket_concurrency():
    """
    Test that multiple tasks can run concurrently over a single WebSocket connection.
    """
    client = TestClient(app)
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        num_tasks = 5
        call_ids = []
        
        # 1. Start multiple tasks
        for i in range(num_tasks):
            req_id = f"req_{i}"
            websocket.send_json({
                "type": "start",
                "tool_name": "long_audit",
                "args": {"duration": 1},
                "request_id": req_id
            })
            
            # Receive task_started for each
            found_start = False
            for _ in range(10):
                data = websocket.receive_json()
                if data["type"] == "task_started" and data.get("request_id") == req_id:
                    call_ids.append(data["call_id"])
                    found_start = True
                    break
            assert found_start, f"Task {i} failed to start"

        assert len(call_ids) == num_tasks
        
        # 2. Collect results for all tasks
        results_received = set()
        for _ in range(200):
            try:
                data = websocket.receive_json()
                if data["type"] == "result":
                    results_received.add(data["call_id"])
                
                if len(results_received) == num_tasks:
                    break
            except Exception:
                break
                
        assert len(results_received) == num_tasks
        for cid in call_ids:
            assert cid in results_received

def test_websocket_interleaved_stop():
    """
    Test starting two tasks and stopping one while the other continues.
    """
    client = TestClient(app)
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
        # Start Task A
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 5},
            "request_id": "req_A"
        })
        data = websocket.receive_json()
        while data["type"] != "task_started":
            data = websocket.receive_json()
        call_id_a = data["call_id"]
        
        # Start Task B
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 1},
            "request_id": "req_B"
        })
        data = websocket.receive_json()
        while data["type"] != "task_started":
            data = websocket.receive_json()
        call_id_b = data["call_id"]
        
        # Stop Task A
        websocket.send_json({
            "type": "stop",
            "call_id": call_id_a,
            "request_id": "stop_A"
        })
        
        found_stop_success_a = False
        found_result_b = False
        
        for _ in range(100):
            data = websocket.receive_json()
            if data["type"] == "stop_success" and data.get("call_id") == call_id_a:
                found_stop_success_a = True
            if data["type"] == "result" and data.get("call_id") == call_id_b:
                found_result_b = True
                
            if found_stop_success_a and found_result_b:
                break
                
        assert found_stop_success_a
        assert found_result_b

def test_websocket_concurrent_input():
    """
    Tests that multiple tasks can wait for and receive input concurrently.
    """
    client = TestClient(app)
    with client.websocket_connect(f"/ws?api_key={API_KEY}") as websocket:
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
                    "value": "yes",
                    "request_id": f"provide_{cid}"
                })
            
            if data["type"] == "result":
                results_received.add(cid)
            
            if len(results_received) == 2:
                break
        
        assert len(waiting_for_ids) == 2, "Both tasks should have requested input"
        assert len(results_received) == 2, "Both tasks should have completed"
