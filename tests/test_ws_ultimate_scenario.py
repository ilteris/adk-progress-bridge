import sys
import os
import json
import pytest
import asyncio
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

def test_websocket_ultimate_scenario():
    """
    ULTIMATE SCENARIO:
    1. Connect via WS.
    2. list_tools and verify.
    3. Start an interactive_task (Task A).
    4. Start a long_audit (Task B) concurrently.
    5. Receive input_request from Task A.
    6. Receive progress from Task B.
    7. Provide input to Task A.
    8. Stop Task B.
    9. Verify Task A completes with result.
    10. Verify Task B was stopped.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. list_tools
        websocket.send_json({"type": "list_tools", "request_id": "req-1"})
        data = websocket.receive_json()
        assert data["type"] == "tools_list"
        assert "interactive_task" in data["tools"]
        assert data["request_id"] == "req-1"

        # 2. Start Task A (Interactive)
        websocket.send_json({
            "type": "start",
            "tool_name": "interactive_task",
            "request_id": "req-2"
        })
        
        call_id_a = None
        while True:
            data = websocket.receive_json()
            if data["type"] == "task_started" and data["request_id"] == "req-2":
                call_id_a = data["call_id"]
                break
        assert call_id_a is not None

        # 3. Start Task B (Long)
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 5},
            "request_id": "req-3"
        })
        
        call_id_b = None
        while True:
            data = websocket.receive_json()
            if data["type"] == "task_started" and data["request_id"] == "req-3":
                call_id_b = data["call_id"]
                break
        assert call_id_b is not None

        # 4. Wait for input request from A and progress from B
        has_input_req = False
        has_progress_b = False
        for _ in range(50):  # Receive up to 50 events
            data = websocket.receive_json()
            if data["type"] == "input_request" and data["call_id"] == call_id_a:
                has_input_req = True
            if data["type"] == "progress" and data["call_id"] == call_id_b:
                has_progress_b = True
            
            if has_input_req and has_progress_b:
                break
        
        assert has_input_req, "Should have received input request from Task A"
        assert has_progress_b, "Should have received progress from Task B"

        # 5. Provide input to Task A
        websocket.send_json({
            "type": "input",
            "call_id": call_id_a,
            "value": "yes",
            "request_id": "req-4"
        })
        
        while True:
            data = websocket.receive_json()
            if data["type"] == "input_success" and data["request_id"] == "req-4":
                break

        # 6. Stop Task B
        websocket.send_json({
            "type": "stop",
            "call_id": call_id_b,
            "request_id": "req-5"
        })
        
        # 7. Collect final events
        final_results = {}
        for _ in range(50):
            data = websocket.receive_json()
            etype = data["type"]
            cid = data.get("call_id")
            
            if etype == "result" and cid == call_id_a:
                final_results["a"] = data["payload"]
            if etype == "stop_success" and cid == call_id_b:
                final_results["b_stopped"] = True
            if etype == "progress" and cid == call_id_b and data["payload"].get("step") == "Cancelled":
                final_results["b_cancelled_msg"] = True
            
            if "a" in final_results and "b_stopped" in final_results:
                break
        
        assert "a" in final_results
        assert final_results["a"]["status"] == "complete"
        assert "user approval" in final_results["a"]["message"]
        assert final_results["b_stopped"] is True
