import pytest
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX, MAX_CONCURRENT_TASKS

from fastapi.testclient import TestClient

def test_build_info_metric():
    client = TestClient(app)
    
    # Check /health first
    response = client.get("/health")
    data = response.json()
    assert data["version"] == APP_VERSION
    assert data["git_commit"] == GIT_COMMIT
    
    # Check prometheus metrics
    response = client.get("/metrics")
    expected = f'adk_build_info{{git_commit="{GIT_COMMIT}",version="{APP_VERSION}"}} 1.0'
    assert expected in response.text
