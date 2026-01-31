import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app, MAX_CONCURRENT_TASKS

def test_health_v325_metadata():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.1.4"
    assert data["git_commit"] == "7e023a1"
    assert data["operational_apex"] == "SUPREME ABSOLUTE APEX"
    assert data["config"]["max_concurrent_tasks"] == MAX_CONCURRENT_TASKS

def test_version_v325():
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.1.4"
    assert data["git_commit"] == "7e023a1"

def test_concurrency_limit_rest():
    client = TestClient(app)
    # This is hard to test fully without mocking the registry or actually starting 100 tasks,
    # but we can verify the constant is exposed in health.
    response = client.get("/health")
    assert response.json()["config"]["max_concurrent_tasks"] == 100

@pytest.mark.asyncio
async def test_list_active_tasks_v325():
    # Simple verification that list_active_tasks still works in v325
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-api-key") as websocket:
        websocket.send_json({
            "type": "list_active_tasks",
            "request_id": "v325-req"
        })
        resp = websocket.receive_json()
        assert resp["type"] == "active_tasks_list"
        assert isinstance(resp["tasks"], list)
