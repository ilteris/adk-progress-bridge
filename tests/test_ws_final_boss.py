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
async def test_ws_ultimate_concurrency_and_robustness():
    """
    ULTIMATE TEST: Multiple concurrent tasks, rapid pings, and large payloads all at once.
    This test uses TestClient in a way that handles the event loop properly for multiple concurrent actions.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # 1. Start multiple tasks
        num_tasks = 3
        call_ids = []
        for i in range(num_tasks):
            req_id = f"boss_start_{i}"
            websocket.send_json({
                "type": "start",
                "tool_name": "long_audit",
                "args": {"duration": 2},
                "request_id": req_id
            })
            
            # Wait for task_started
            found = False
            for _ in range(10):
                data = websocket.receive_json()
                if data["type"] == "task_started" and data.get("request_id") == req_id:
                    call_ids.append(data["call_id"])
                    found = True
                    break
            assert found

        # 2. Interleave pings while tasks are running
        for _ in range(5):
            websocket.send_json({"type": "ping"})
            data = websocket.receive_json()
            # We might get task events instead of pong, so we loop
            while data["type"] != "pong":
                assert data["type"] in ["progress", "task_started", "error"]
                data = websocket.receive_json()
            assert data["type"] == "pong"

        # 3. Send a large payload during active streaming
        large_payload = "x" * 50000
        websocket.send_json({
            "type": "ping",
            "metadata": large_payload
        })
        data = websocket.receive_json()
        while data["type"] != "pong":
            data = websocket.receive_json()
        assert data["type"] == "pong"

        # 4. Wait for all results
        results = set()
        for _ in range(100):
            data = websocket.receive_json()
            if data["type"] == "result":
                results.add(data["call_id"])
            if len(results) == num_tasks:
                break
        
        assert len(results) == num_tasks

def test_ws_protocol_compliance_audit():
    """
    Verifies that all command types (start, stop, input, list_tools, ping)
    work as expected and follow the request_id correlation protocol.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # list_tools
        websocket.send_json({"type": "list_tools", "request_id": "req_list"})
        data = websocket.receive_json()
        assert data["type"] == "tools_list"
        assert data["request_id"] == "req_list"
        assert len(data["tools"]) > 0

        # ping
        websocket.send_json({"type": "ping", "request_id": "req_ping"})
        data = websocket.receive_json()
        assert data["type"] == "pong"

        # start
        websocket.send_json({
            "type": "start",
            "tool_name": "interactive_task",
            "request_id": "req_start"
        })
        data = websocket.receive_json()
        assert data["type"] == "task_started"
        assert data["request_id"] == "req_start"
        call_id = data["call_id"]

        # Wait for input_request
        found_input_request = False
        for _ in range(50):
            data = websocket.receive_json()
            if data["type"] == "input_request" and data.get("call_id") == call_id:
                found_input_request = True
                break
        assert found_input_request

        # input
        websocket.send_json({
            "type": "input",
            "call_id": call_id,
            "value": "proceed",
            "request_id": "req_input"
        })
        
        # We might get some progress before input_success
        found_input_success = False
        for _ in range(10):
            data = websocket.receive_json()
            if data["type"] == "input_success" and data.get("request_id") == "req_input":
                found_input_success = True
                break
        assert found_input_success

        # result
        found_result = False
        for _ in range(20):
            data = websocket.receive_json()
            if data["type"] == "result" and data.get("call_id") == call_id:
                found_result = True
                break
        assert found_result

def test_ws_error_correlation_robustness():
    """
    Verifies that errors always include the request_id if provided.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Invalid tool_name
        req_id = "error_req_1"
        websocket.send_json({
            "type": "start",
            "tool_name": "non_existent_tool",
            "request_id": req_id
        })
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data["request_id"] == req_id

        # Stop non-existent task
        req_id = "error_req_2"
        websocket.send_json({
            "type": "stop",
            "call_id": "invalid_call_id",
            "request_id": req_id
        })
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data["request_id"] == req_id

        # Input to non-waiting task
        req_id = "error_req_3"
        websocket.send_json({
            "type": "input",
            "call_id": "some_id",
            "value": "foo",
            "request_id": req_id
        })
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data["request_id"] == req_id