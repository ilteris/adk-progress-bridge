import sys
import os
import json
import pytest
from fastapi.testclient import TestClient

# Add the project root to sys.path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

def test_context_switch_audit_tool_ws():
    """
    Verifies that the new context_switch_audit tool works over WebSocket.
    """
    with TestClient(app) as client:
        with client.websocket_connect("/ws?api_key=test_key") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"
            
            request_id = "v650-context-audit"
            websocket.send_json({
                "type": "start",
                "tool_name": "context_switch_audit",
                "args": {"samples": 2},
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
                    if data["payload"].get("step") == "Sampling context switches":
                        assert "metadata" in data["payload"]
                        assert "voluntary" in data["payload"]["metadata"]
                        assert "involuntary" in data["payload"]["metadata"]
                elif data["type"] == "result":
                    assert data["payload"]["status"] == "audit_complete"
                    assert "final_ctx_switches" in data["payload"]
                    result_received = True
                    break
                elif data["type"] == "error":
                    pytest.fail(f"Error received: {data['payload']}")
            
            assert progress_received, "Did not receive progress updates"
            assert result_received, "Did not receive final result"

def test_v650_metadata_verification():
    """
    Verifies that the version and metadata are correctly updated for v650.
    """
    with TestClient(app) as client:
        response = client.get("/version")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "2.7.6"
        assert "v650" in data["status"]
