import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set API key for tests before importing app
API_KEY = "test_secret_key"
os.environ["BRIDGE_API_KEY"] = API_KEY

from backend.app.main import app

client = TestClient(app)
headers = {"X-API-Key": API_KEY}

def test_api_validation_success():
    # duration is 10 by default, but let's pass it
    response = client.post("/start_task/long_audit", json={"args": {"duration": 5}}, headers=headers)
    assert response.status_code == 200
    assert "call_id" in response.json()

def test_api_validation_coercion():
    # Pydantic should coerce "5" to 5
    response = client.post("/start_task/long_audit", json={"args": {"duration": "5"}}, headers=headers)
    assert response.status_code == 200
    assert "call_id" in response.json()

def test_api_validation_invalid_type():
    response = client.post("/start_task/long_audit", json={"args": {"duration": "not-an-int"}}, headers=headers)
    assert response.status_code == 400
    # The detail will be the string representation of Pydantic's ValidationError
    assert "validation error" in response.json()["detail"].lower()

def test_api_validation_extra_arg():
    # Extra arguments should be ignored or cause error depending on Config.extra
    # By default, pydantic ignores extra args
    response = client.post("/start_task/long_audit", json={"args": {"duration": 5, "unknown": "arg"}}, headers=headers)
    assert response.status_code == 200

def test_api_validation_missing_args():
    # If a tool has required args, missing them should cause 400
    # But long_audit has duration=10 as default
    response = client.post("/start_task/long_audit", json={"args": {}}, headers=headers)
    assert response.status_code == 200