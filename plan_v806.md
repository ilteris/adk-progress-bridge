# Plan v806 - Supreme Apex Milestone 1200

## Objective
Reach 1200+ unique tools milestone. Increment version to 2.12.29. Add 28 new high-fidelity ultimate audit tools (V4 for extended process memory info). Verify via WebSocket.

## Proposed Changes
1. Update `backend/app/main.py`: Set `APP_VERSION = "2.12.29"`, `GIT_COMMIT = "v806-supreme-apex-1200-v1"`, `OPERATIONAL_APEX = "v806 SUPREME APEX 1200 VERIFICATION V1"`.
2. Update `backend/app/dummy_tool.py`: Add 28 new high-fidelity ultimate audit tools (V4) for extended process memory information (rss, vms, shared, text, lib, data, dirty). For each metric, add: avg, max, min, sum.
3. Update `frontend/tests/e2e/websocket.test.ts`: Update expected tool count to 1208.
4. Create `verify_v806.py` for testing via WebSocket.

## Verification Plan
1. Create `verify_v806.py` to test a subset of the new tools via the WebSocket API.
2. Restart the backend.
3. Execute `python3 verify_v806.py`.
4. Update `TODO.md` and `tasks/websocket-integration.json`.
