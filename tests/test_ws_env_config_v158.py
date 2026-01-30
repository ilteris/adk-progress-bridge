import os
import sys
from unittest.mock import patch

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_websocket_env_config_v158():
    """
    Verifies that WebSocket constants can be configured via environment variables.
    Note: We need to reload the module or mock os.getenv before import to test this properly,
    but since it's already imported in other tests, we'll check the current values
    and then mock os.getenv for a fresh import simulation if needed.
    """
    # For this test, we'll just verify the logic by mocking os.getenv and re-importing main
    with patch.dict(os.environ, {
        "WS_HEARTBEAT_TIMEOUT": "99.0",
        "CLEANUP_INTERVAL": "45.0",
        "STALE_TASK_MAX_AGE": "600.0",
        "WS_MESSAGE_SIZE_LIMIT": "2048576"
    }):
        # Use importlib to reload the module
        import importlib
        import backend.app.main
        importlib.reload(backend.app.main)
        
        from backend.app.main import WS_HEARTBEAT_TIMEOUT, CLEANUP_INTERVAL, STALE_TASK_MAX_AGE, WS_MESSAGE_SIZE_LIMIT
        
        assert WS_HEARTBEAT_TIMEOUT == 99.0
        assert CLEANUP_INTERVAL == 45.0
        assert STALE_TASK_MAX_AGE == 600.0
        assert WS_MESSAGE_SIZE_LIMIT == 2048576

    # Restore defaults for other tests by reloading again without env vars
    importlib.reload(backend.app.main)
