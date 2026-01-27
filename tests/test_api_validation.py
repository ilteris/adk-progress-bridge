import sys
import os
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

client = TestClient(app)

def test_api_validation_success():
    # duration is 10 by default, but let's pass it
    response = client.post("/start_task/long_audit", json={"duration": 5})
    assert response.status_code == 200
    assert "call_id" in response.json()

def test_api_validation_coercion():
    # Pydantic should coerce "5" to 5
    response = client.post("/start_task/long_audit", json={"duration": "5"})
    assert response.status_code == 200
    assert "call_id" in response.json()

def test_api_validation_invalid_type():
    response = client.post("/start_task/long_audit", json={"duration": "not-an-int"})
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert any(d["loc"] == ["duration"] for d in detail)

def test_api_validation_extra_arg():
    response = client.post("/start_task/long_audit", json={"extra": "bad"})
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert any(d["loc"] == ["extra"] for d in detail)

def test_api_validation_tool_not_found():
    response = client.post("/start_task/non_existent", json={})
    assert response.status_code == 404

if __name__ == "__main__":
    test_api_validation_success()
    print("test_api_validation_success passed")
    test_api_validation_coercion()
    print("test_api_validation_coercion passed")
    test_api_validation_invalid_type()
    print("test_api_validation_invalid_type passed")
    test_api_validation_extra_arg()
    print("test_api_validation_extra_arg passed")
    test_api_validation_tool_not_found()
    print("test_api_validation_tool_not_found passed")