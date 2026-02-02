from fastapi.testclient import TestClient
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX
import pytest

def test_v677_minimal():
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        websocket.receive_json() # connected
        websocket.send_json({
            "type": "start",
            "tool_name": "system_net_io_dropin_total_audit",
            "args": {"samples": 1},
            "request_id": "req1"
        })
        # Consume messages until result
        while True:
            data = websocket.receive_json()
            if data.get("type") == "result":
                assert data["payload"]["status"] == "audit_complete"
                break
            if data.get("type") == "error":
                pytest.fail(f"Error: {data}")
