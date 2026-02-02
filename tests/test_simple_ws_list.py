from fastapi.testclient import TestClient
from backend.app.main import app, APP_VERSION, GIT_COMMIT, OPERATIONAL_APEX

def test_list_tools():
    client = TestClient(app)
    with client.websocket_connect("/ws?api_key=test-key") as websocket:
        websocket.receive_json() # connected
        websocket.send_json({"type": "list_tools"})
        data = websocket.receive_json()
        assert data["type"] == "tools_list"
        assert len(data["tools"]) >= 147
