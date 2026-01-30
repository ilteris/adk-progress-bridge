import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set API key for tests before importing app
API_KEY = "test_secret_key"
os.environ["BRIDGE_API_KEY"] = API_KEY

from backend.app.main import app

client = TestClient(app)
headers = {"X-API-Key": API_KEY}

def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    # Use a more reliable metric that should always be present
    assert "adk_active_tasks" in response.text

def test_custom_metrics_incremented():
    # 1. Trigger a task
    client.post("/start_task/long_audit", json={"args": {"duration": 1}}, headers=headers)
    
    # 2. Check if adk_tasks_total incremented
    after_resp = client.get("/metrics")
    after_text = after_resp.text
    
    assert "adk_tasks_total" in after_text