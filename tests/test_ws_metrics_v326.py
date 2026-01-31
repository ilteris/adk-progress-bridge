import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app, MAX_CONCURRENT_TASKS, APP_VERSION, GIT_COMMIT

def test_health_v326_metadata():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == APP_VERSION
    assert data["git_commit"] == GIT_COMMIT
    assert data["operational_apex"] == "SUPREME ABSOLUTE APEX OMEGA"
    assert data["config"]["max_concurrent_tasks"] == MAX_CONCURRENT_TASKS

def test_version_v326():
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == APP_VERSION
    assert data["git_commit"] == GIT_COMMIT

@pytest.mark.asyncio
async def test_unknown_ws_message_logging_v326():
    client = TestClient(app)
    # Using a shorter timeout for receiving to avoid hanging forever
    with client.websocket_connect("/ws?api_key=test-api-key") as websocket:
        websocket.send_json({
            "type": "unknown_type_xyz",
            "request_id": "v326-unknown"
        })
        resp = websocket.receive_json()
        assert resp["type"] == "error"
        assert "Unknown message type" in resp["payload"]["detail"]
        assert resp["request_id"] == "v326-unknown"

@pytest.mark.asyncio
async def test_invalid_json_ws_v326():
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-api-key") as websocket:
        websocket.send_text("not a json")
        resp = websocket.receive_json()
        assert resp["type"] == "error"
        assert "Invalid JSON" in resp["payload"]["detail"]
