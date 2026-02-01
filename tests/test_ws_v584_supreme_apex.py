import sys
import os
import json
import pytest
import asyncio
import time
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

@pytest.mark.asyncio
async def test_ws_v649_supreme_apex_comprehensive():
    """
    V584 SUPREME APEX VERIFICATION:
    1. Verify connection handshake (connected message)
    2. Verify list_tools & list_active_tasks protocol
    3. Verify health data includes v2.7.5 and v649 markers
    4. Verify concurrent task execution and isolation
    5. Verify request_id correlation across all message types
    """
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        # 1. Connection Handshake
        data = websocket.receive_json()
        assert data["type"] == "connected"
        assert data["status"] == "ready"

        # 2. Protocol: list_tools
        req_id_list = "req_v649_list"
        websocket.send_json({"type": "list_tools", "request_id": req_id_list})
        data = websocket.receive_json()
        while data["type"] != "tools_list":
            data = websocket.receive_json()
        assert data["type"] == "tools_list"
        assert data["request_id"] == req_id_list
        assert "long_audit" in data["tools"]

        # 3. Protocol: get_health & Version Check
        req_id_health = "req_v649_health"
        websocket.send_json({"type": "get_health", "request_id": req_id_health})
        data = websocket.receive_json()
        while data["type"] != "health_data":
            data = websocket.receive_json()
        assert data["type"] == "health_data"
        assert data["request_id"] == req_id_health
        health = data["data"]
        assert health["version"] == "2.7.5"
        assert "v649" in health["operational_apex"]
        assert "build_timestamp" in health

        # 4. Concurrent Task Execution
        num_tasks = 5
        call_ids = []
        for i in range(num_tasks):
            req_id = f"v649_start_{i}"
            websocket.send_json({
                "type": "start",
                "tool_name": "security_scan",
                "request_id": req_id
            })
            
            # Expect task_started
            found_start = False
            for _ in range(20): # Increased loop for robustness
                d = websocket.receive_json()
                if d["type"] == "task_started" and d.get("request_id") == req_id:
                    call_ids.append(d["call_id"])
                    found_start = True
                    break
            assert found_start

        # 5. list_active_tasks
        req_id_active = "req_v649_active"
        websocket.send_json({"type": "list_active_tasks", "request_id": req_id_active})
        
        data = websocket.receive_json()
        while data["type"] != "active_tasks_list":
            data = websocket.receive_json()
            
        assert data["type"] == "active_tasks_list"
        assert data["request_id"] == req_id_active
        active_ids = [t["call_id"] for t in data["tasks"]]
        for cid in call_ids:
            assert cid in active_ids

        # 6. Wait for completion of all tasks
        results_received = 0
        for _ in range(500): # Plenty of messages to consume
            d = websocket.receive_json()
            if d["type"] == "result":
                results_received += 1
            if results_received == num_tasks:
                break
        
        assert results_received == num_tasks

@pytest.mark.asyncio
async def test_ws_v649_boundary_conditions():
    """
    Verify boundary conditions:
    1. Message size limit (1MB)
    2. Invalid JSON handling
    3. Tool not found handling with request_id
    """
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        websocket.receive_json() # connected

        # 1. Message too large
        large_data = "x" * (1024 * 1024 + 100)
        websocket.send_text(json.dumps({"type": "ping", "data": large_data}))
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "too large" in data["payload"]["detail"]

        # 2. Invalid JSON
        websocket.send_text("not a json")
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "Invalid JSON" in data["payload"]["detail"]

        # 3. Tool not found
        req_id = "v649_tool_not_found"
        websocket.send_json({
            "type": "start",
            "tool_name": "ghost_tool",
            "request_id": req_id
        })
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data["request_id"] == req_id
        assert "Tool not found" in data["payload"]["detail"]

@pytest.mark.asyncio
async def test_ws_v649_multi_connection_concurrency():
    """
    Verify that multiple concurrent WebSocket connections can each run tasks independently.
    """
    client = TestClient(app)
    num_clients = 3
    num_tasks_per_client = 2
    
    with client.websocket_connect("/ws?api_key=test-key") as ws1, \
         client.websocket_connect("/ws?api_key=test-key") as ws2, \
         client.websocket_connect("/ws?api_key=test-key") as ws3:
        
        websockets = [ws1, ws2, ws3]
        for ws in websockets:
            assert ws.receive_json()["type"] == "connected"
            
        # Start tasks for all clients
        for idx, ws in enumerate(websockets):
            for i in range(num_tasks_per_client):
                ws.send_json({
                    "type": "start",
                    "tool_name": "security_scan",
                    "request_id": f"client_{idx}_task_{i}"
                })
        
        # Verify task_started for all
        for idx, ws in enumerate(websockets):
            for i in range(num_tasks_per_client):
                found = False
                for _ in range(20):
                    d = ws.receive_json()
                    if d["type"] == "task_started":
                        found = True
                        break
                assert found

        # Verify list_active_tasks from any client sees all tasks
        websockets[0].send_json({"type": "list_active_tasks", "request_id": "multi_check"})
        data = websockets[0].receive_json()
        while data["type"] != "active_tasks_list":
            data = websockets[0].receive_json()
        
        assert len(data["tasks"]) >= num_clients * num_tasks_per_client