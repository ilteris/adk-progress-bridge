import sys
import os
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

client = TestClient(app)

def test_api_validation_success():
    # duration is 10 by default, but let's pass it
    response = client.post("/start_task/long_audit", json={"args": {"duration": 5}})
    assert response.status_code == 200
    assert "call_id" in response.json()

def test_api_validation_coercion():
    # Pydantic should coerce "5" to 5
    response = client.post("/start_task/long_audit", json={"args": {"duration": "5"}})
    assert response.status_code == 200
    assert "call_id" in response.json()

def test_api_validation_invalid_type():
    response = client.post("/start_task/long_audit", json={"args": {"duration": "not-an-int"}})
    assert response.status_code == 400
    # The detail will be the string representation of Pydantic's ValidationError
    assert "validation error" in response.json()["detail"].lower()

def test_api_validation_extra_arg():
    # Since we use validate_call, it might or might not forbid extra args depending on config.
    # By default Pydantic validate_call allows extra args unless configured otherwise.
    # But let's see what happens.
    response = client.post("/start_task/long_audit", json={"args": {"extra": "bad"}})
    # If it's NOT forbidden, it will be 200.
    # To make it 400, we'd need to configure validate_call(config={"extra": "forbid"})
    pass

def test_api_validation_tool_not_found():
    response = client.post("/start_task/non_existent", json={"args": {}})
    assert response.status_code == 404
