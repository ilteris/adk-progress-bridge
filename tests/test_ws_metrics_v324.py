import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app

def test_health_v324_metadata():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.1.3"
    assert data["git_commit"] == "6e9b58a"
    assert data["operational_apex"] == "SUPREME ABSOLUTE APEX"

def test_version_v324():
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.1.3"
    assert data["git_commit"] == "6e9b58a"

def test_list_active_tasks_rest():
    client = TestClient(app)
    # Start a task first
    start_resp = client.post("/start_task/long_audit", json={"args": {"duration": 5}})
    assert start_resp.status_code == 200
    call_id = start_resp.json()["call_id"]
    
    # List tasks
    response = client.get("/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert any(t["call_id"] == call_id for t in tasks)
    
    # Cleanup: remove task
    client.post(f"/stop_task/{call_id}")

@pytest.mark.asyncio
async def test_list_active_tasks_ws():
    # We need a real websocket for this, or use TestClient with websocket_connect
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-api-key") as websocket:
        # Start a task
        websocket.send_json({
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 5},
            "request_id": "req-1"
        })
        resp = websocket.receive_json()
        assert resp["type"] == "task_started"
        call_id = resp["call_id"]
        
        # List active tasks
        websocket.send_json({
            "type": "list_active_tasks",
            "request_id": "req-2"
        })
        
        # We might get some progress updates before the list response
        # We loop until we find our response or a timeout (implicitly handled by receive_json blocking)
        found = False
        for _ in range(10): # Try 10 times to find the response
            resp = websocket.receive_json()
            if resp["type"] == "active_tasks_list":
                assert any(t["call_id"] == call_id for t in resp["tasks"])
                found = True
                break
        
        assert found, "Did not receive active_tasks_list message"