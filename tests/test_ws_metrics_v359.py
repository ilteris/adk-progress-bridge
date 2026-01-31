import pytest
from fastapi.testclient import TestClient
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX
import time
import json

client = TestClient(app)

@pytest.mark.asyncio
async def test_v359_health_metrics():
    """Verify v359 metrics are present in the health data."""
    # Wait for rate calculation window
    time.sleep(1.1)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    assert data["version"] == "1.4.9"
    assert data["operational_apex"] == "THE TRANSCENDENCE"
    assert data["git_commit"] == "v359-the-transcendence"
    
    # Check page fault rates
    assert "page_faults" in data
    assert "minor_rate_per_sec" in data["page_faults"]
    assert "major_rate_per_sec" in data["page_faults"]
    assert isinstance(data["page_faults"]["minor_rate_per_sec"], (int, float))
    
    # Check WS error metrics
    assert "ws_binary_frames_rejected" in data
    assert "ws_connection_errors" in data
    assert isinstance(data["ws_binary_frames_rejected"], int)
    assert isinstance(data["ws_connection_errors"], int)

@pytest.mark.asyncio
async def test_v359_prometheus_metrics():
    """Verify v359 metrics are present in the /metrics endpoint."""
    time.sleep(1.1)
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    assert "adk_system_page_fault_minor_rate_per_sec" in content
    assert "adk_system_page_fault_major_rate_per_sec" in content
    assert "adk_ws_binary_frames_rejected_total" in content
    assert "adk_ws_connection_errors_total" in content
    assert 'adk_build_info{git_commit="v359-the-transcendence",version="1.4.9"}' in content

@pytest.mark.asyncio
async def test_ws_binary_rejection_metric_v359():
    """Verify binary frame rejection increments the counter."""
    with client.websocket_connect("/ws") as websocket:
        websocket.send_bytes(b"binary data")
        resp = websocket.receive_json()
        assert resp["type"] == "error"
        assert "Binary messages are not supported" in resp["payload"]["detail"]
        
    response = client.get("/health")
    data = response.json()
    assert data["ws_binary_frames_rejected"] >= 1
