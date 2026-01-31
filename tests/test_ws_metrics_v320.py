import pytest
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app, ACTIVE_WS_CONNECTIONS

client = TestClient(app)

def test_health_active_ws_connections():
    # Initial state
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "active_ws_connections" in data
    initial_connections = data["active_ws_connections"]
    
    # We can't easily test WebSocket with TestClient in a way that increments the Gauge in the app instance 
    # because TestClient might use a different instance or mock it.
    # But since we are using the imported 'app', it should be the same.
    # However, TestClient for WebSocket is synchronous.
    
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        # It should be initial + 1
        assert data["active_ws_connections"] == initial_connections + 1
        
    # After closing, it should be back to initial
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["active_ws_connections"] == initial_connections

def test_metrics_endpoint_has_ws_metric():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "adk_active_ws_connections" in response.text
