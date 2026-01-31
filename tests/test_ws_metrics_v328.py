import pytest
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX, MAX_CONCURRENT_TASKS

import asyncio
import json
import time
from fastapi.testclient import TestClient

from backend.app.bridge import registry

client = TestClient(app)

@pytest.mark.asyncio
async def test_health_metrics_v328():
    """Verify that the health endpoint returns the new v328 metrics."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    # Check version and commit (updated to use constants to support v329 progression)
    assert data["version"] == APP_VERSION
    assert data["git_commit"] == GIT_COMMIT
    
    # Check new system metrics
    assert "cpu_usage_percent" in data
    assert "python_implementation" in data
    assert "peak_registry_size" in data
    
    # Verify values are reasonable
    assert isinstance(data["cpu_usage_percent"], (int, float))
    assert data["python_implementation"] in ["CPython", "PyPy"]
    assert data["peak_registry_size"] >= 0

@pytest.mark.asyncio
async def test_peak_registry_tracking():
    """Verify that peak_registry_size correctly tracks the maximum concurrent tasks."""
    # Reset peak for testing if possible (it's a property, so we can't easily reset without internal access)
    # Instead, we just verify it's at least as large as current count
    initial_peak = registry.peak_active_tasks
    current_count = registry.active_task_count
    
    # Start enough tasks to definitely exceed the previous peak, or just verify current behavior
    # Let's just start 10 tasks to be sure we hit a new peak if the old one was small
    call_ids = []
    for _ in range(10):
        response = client.post("/start_task/long_audit", json={"args": {"duration": 5}})
        assert response.status_code == 200
        call_ids.append(response.json()["call_id"])
    
    new_peak = registry.peak_active_tasks
    assert new_peak >= 10
    assert new_peak >= initial_peak
    
    response = client.get("/health")
    data = response.json()
    assert data["peak_registry_size"] == new_peak
    
    # Cleanup
    for cid in call_ids:
        await registry.remove_task(cid)

@pytest.mark.asyncio
async def test_prometheus_metrics_v328():
    """Verify that the /metrics endpoint includes the new peak gauge."""
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    assert "adk_peak_active_tasks" in content