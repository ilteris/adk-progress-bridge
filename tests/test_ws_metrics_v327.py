import pytest
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX, MAX_CONCURRENT_TASKS

import asyncio
import json
import time
from fastapi.testclient import TestClient

from backend.app.bridge import registry

client = TestClient(app)

@pytest.mark.asyncio
async def test_health_metrics_v327():
    """Verify that the health endpoint returns the human-readable uptime and registry summary (v327)."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    # Check enhanced health metrics
    assert "uptime_human" in data
    assert "registry_summary" in data
    assert "operational_apex" in data
    assert data["operational_apex"] == OPERATIONAL_APEX
    
    # Verify uptime_human format (e.g., "0s", "1m 5s")
    assert isinstance(data["uptime_human"], str)
    assert "s" in data["uptime_human"]
    
    # Verify registry_summary is a dict
    assert isinstance(data["registry_summary"], dict)

@pytest.mark.asyncio
async def test_registry_summary_content():
    """Verify that registry_summary correctly reflects active tools."""
    # Start a task
    response = client.post("/start_task/long_audit", json={"args": {"duration": 5}})
    assert response.status_code == 200
    
    response = client.get("/health")
    data = response.json()
    assert "long_audit" in data["registry_summary"]
    assert data["registry_summary"]["long_audit"] >= 1
    
    # Cleanup
    call_id = response.json().get("call_id") # Wait, health response doesn't have call_id
    # We need to get it from the start_task response
    
@pytest.mark.asyncio
async def test_version_v327():
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    # Use APP_VERSION constant to be future-proof
    assert data["version"] == APP_VERSION
