import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
import time

client = TestClient(app)

@pytest.mark.asyncio
async def test_v358_health_metrics():
    """Verify v358 metrics are present in the health data."""
    # Wait a bit to allow rate calculations to have data (at least 1s)
    time.sleep(1.1)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    # Check version and apex
    assert data["version"] >= "1.4.8"
    assert len(data["operational_apex"]) > 0
    
    # Check system CPU stats rates
    assert "system_cpu_stats" in data
    assert "context_switch_rate_per_sec" in data["system_cpu_stats"]
    assert "interrupt_rate_per_sec" in data["system_cpu_stats"]
    
    assert isinstance(data["system_cpu_stats"]["context_switch_rate_per_sec"], (int, float))
    assert isinstance(data["system_cpu_stats"]["interrupt_rate_per_sec"], (int, float))

@pytest.mark.asyncio
async def test_v358_prometheus_metrics():
    """Verify v358 metrics are present in the /metrics endpoint."""
    time.sleep(1.1)
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    assert "adk_system_cpu_context_switch_rate_per_sec" in content
    assert "adk_system_cpu_interrupt_rate_per_sec" in content
    assert "adk_ws_message_size_bytes_bucket" in content

@pytest.mark.asyncio
async def test_ws_message_size_tracking_v358():
    """Verify v358 WS message size tracking."""
    with client.websocket_connect("/ws") as websocket:
        # Send a message of known size
        msg = {"type": "ping", "request_id": "v358_test_ping"}
        websocket.send_json(msg)
        response = websocket.receive_json()
        assert response["type"] == "pong"
        
        # Check metrics
        health_response = client.get("/health")
        data = health_response.json()
        assert data["version"] >= "1.4.8"
        
        # Check /metrics for histogram
        metrics_response = client.get("/metrics")
        assert "adk_ws_message_size_bytes_count" in metrics_response.text
        assert "adk_ws_message_size_bytes_sum" in metrics_response.text