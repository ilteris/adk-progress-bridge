import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app
from backend.app import auth

client = TestClient(app)

@pytest.fixture
def enable_auth(monkeypatch):
    monkeypatch.setenv("BRIDGE_API_KEY", "test-secret-key")
    # We need to reload the BRIDGE_API_KEY in the auth module because it's evaluated at import time
    monkeypatch.setattr(auth, "BRIDGE_API_KEY", "test-secret-key")
    yield
    monkeypatch.setattr(auth, "BRIDGE_API_KEY", None)

def test_auth_disabled_by_default():
    # When BRIDGE_API_KEY is not set, it should allow access
    response = client.post("/start_task/long_audit", json={"duration": 1})
    assert response.status_code == 200

def test_auth_enabled_no_key(enable_auth):
    response = client.post("/start_task/long_audit", json={"duration": 1})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API Key"

def test_auth_enabled_wrong_key(enable_auth):
    response = client.post("/start_task/long_audit", json={"duration": 1}, headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401

def test_auth_enabled_correct_key(enable_auth):
    response = client.post("/start_task/long_audit", json={"duration": 1}, headers={"X-API-Key": "test-secret-key"})
    assert response.status_code == 200

def test_auth_sse_query_param(enable_auth):
    # First start a task with valid header
    response = client.post("/start_task/long_audit", json={"duration": 1}, headers={"X-API-Key": "test-secret-key"})
    call_id = response.json()["call_id"]
    
    # Try to stream without key
    response = client.get(f"/stream/{call_id}")
    assert response.status_code == 401
    
    # Try to stream with wrong key in query param
    response = client.get(f"/stream/{call_id}?api_key=wrong")
    assert response.status_code == 401
    
    # Try to stream with correct key in query param
    response = client.get(f"/stream/{call_id}?api_key=test-secret-key")
    assert response.status_code == 200

def test_auth_sse_header_fallback(enable_auth):
    # First start a task
    response = client.post("/start_task/long_audit", json={"duration": 1}, headers={"X-API-Key": "test-secret-key"})
    call_id = response.json()["call_id"]
    
    # Try to stream with correct key in header (fallback)
    response = client.get(f"/stream/{call_id}", headers={"X-API-Key": "test-secret-key"})
    assert response.status_code == 200