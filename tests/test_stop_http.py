import sys
import os
import json
import pytest
import asyncio
from fastapi.testclient import TestClient

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

def test_stop_task_http():
    client = TestClient(app)
    
    # 1. Start a task
    response = client.post("/start_task/long_audit", json={"args": {"duration": 10}})
    assert response.status_code == 200
    call_id = response.json()["call_id"]
    
    # 2. Stop the task via POST (as per main.py and spec)
    stop_response = client.post(f"/stop_task/{call_id}")
    assert stop_response.status_code == 200
    assert stop_response.json()["status"] == "stop signal sent"
    
    # 3. Try to stream (should fail as task is removed/closed)
    stream_response = client.get(f"/stream/{call_id}")
    assert stream_response.status_code == 404

def test_stop_task_http_not_found():
    client = TestClient(app)
    response = client.post("/stop_task/non-existent-id")
    assert response.status_code == 404