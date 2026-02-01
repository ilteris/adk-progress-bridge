import sys
import os
import json
import pytest
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

def test_system_config_audit_tool_ws():
    """
    Verifies that the new system_config_audit tool works over WebSocket.
    """
    with TestClient(app) as client:
        with client.websocket_connect("/ws?api_key=test_key") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"
            
            request_id = "v623-audit-test"
            websocket.send_json({
                "type": "start",
                "tool_name": "system_config_audit",
                "request_id": request_id
            })
            
            progress_received = False
            result_received = False
            
            for i in range(50):
                data = websocket.receive_json()
                
                if data["type"] == "task_started":
                    assert data["request_id"] == request_id
                elif data["type"] == "progress":
                    progress_received = True
                elif data["type"] == "result":
                    assert data["payload"]["status"] == "audit_complete"
                    assert "python_version" in data["payload"]
                    assert "cwd" in data["payload"]
                    result_received = True
                    break
                elif data["type"] == "error":
                    pytest.fail(f"Error received: {data['payload']}")
            
            assert progress_received, "Did not receive progress updates"
            assert result_received, "Did not receive final result"

def test_v623_metadata_verification():
    """
    Verifies that the version and metadata are correctly updated for v623.
    """
    with TestClient(app) as client:
        response = client.get("/version")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "2.4.9"
        assert "v623" in data["git_commit"]
        assert "v623" in data["status"]
