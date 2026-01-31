import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

def test_health_v323_metadata():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.1.2"
    assert data["git_commit"] == "2825c9d"
    assert data["operational_apex"] == "SUPREME ABSOLUTE APEX"

def test_version_v323():
    client = TestClient(app)
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.1.2"
    assert data["git_commit"] == "2825c9d"
