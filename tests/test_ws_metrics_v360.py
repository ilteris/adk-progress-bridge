import pytest
from fastapi.testclient import TestClient
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX
from backend.app import auth
import time
import json

client = TestClient(app)

@pytest.fixture
def enable_auth(monkeypatch):
    monkeypatch.setenv("BRIDGE_API_KEY", "test-secret-key")
    # We need to reload the BRIDGE_API_KEY in the auth module because it's evaluated at import time
    monkeypatch.setattr(auth, "BRIDGE_API_KEY", "test-secret-key")
    yield
    monkeypatch.setattr(auth, "BRIDGE_API_KEY", None)

@pytest.mark.asyncio
async def test_v360_health_metrics():
    """Verify v360 metrics are present in the health data."""
    # Wait for rate calculation window
    time.sleep(1.1)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    assert data["version"] == "1.6.0"
    assert data["operational_apex"] == "THE NEBULA"
    assert data["git_commit"] == "v361-the-nebula"
    
    # Check interrupt rates
    assert "system_cpu_stats" in data
    assert "soft_interrupt_rate_per_sec" in data["system_cpu_stats"]
    assert "syscall_rate_per_sec" in data["system_cpu_stats"]
    assert isinstance(data["system_cpu_stats"]["soft_interrupt_rate_per_sec"], (int, float))
    
    # Check WS error breakdown
    assert "ws_connection_errors_breakdown" in data
    assert "auth_failure" in data["ws_connection_errors_breakdown"]
    assert "protocol_error" in data["ws_connection_errors_breakdown"]
    assert isinstance(data["ws_connection_errors_breakdown"]["auth_failure"], int)

@pytest.mark.asyncio
async def test_v360_prometheus_metrics():
    """Verify v360 metrics are present in the /metrics endpoint."""
    time.sleep(1.1)
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    
    assert "adk_system_cpu_soft_interrupt_rate_per_sec" in content
    assert "adk_system_cpu_syscall_rate_per_sec" in content
    assert 'adk_ws_connection_errors_total{error_type="auth_failure"}' in content
    assert 'adk_ws_connection_errors_total{error_type="protocol_error"}' in content
    assert 'adk_build_info{git_commit="v361-the-nebula",version="1.6.0"}' in content

@pytest.mark.asyncio
async def test_ws_auth_error_metric_v360(enable_auth):
    """Verify auth failure increments the counter with correct label."""
    # Use an invalid API key to trigger auth failure
    with client.websocket_connect("/ws?api_key=invalid-key") as websocket:
        # Starlette TestClient raises WebSocketDisconnect on failed handshake in some versions,
        # or we might get a close frame.
        pass
        
    response = client.get("/health")
    data = response.json()
    assert data["ws_connection_errors_breakdown"]["auth_failure"] >= 1