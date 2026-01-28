# Audit Plan - WebSocket Integration & Observability

## Goal
Enhance the WebSocket and SSE implementation with better observability (timestamps) and ensure backend robustness against edge cases (call_id collisions).

## Proposed Changes

### 1. Backend (bridge.py)
- Add `timestamp: float` to `ProgressEvent` model with a default factory using `time.time()`.
- Update `ToolRegistry.store_task` to check if `call_id` already exists and raise a `ValueError` if it does.

### 2. Backend (main.py)
- Add `timestamp: float` to `TaskStartResponse`.
- Update `start_task` and `websocket_endpoint` to handle potential `ValueError` from `store_task`.
- Ensure all outgoing WebSocket messages (including errors and successes) have a `timestamp`.

### 3. Frontend (useAgentStream.ts)
- Update `AgentEvent` interface to include optional `timestamp`.
- Display timestamp in logs if available.

### 4. Verification
- Add `tests/test_call_id_collision.py` to verify collision handling.
- Add `tests/test_timestamp_audit.py` to verify that all events have timestamps.
- Run all existing tests (53 backend, 15 frontend).

## PR Target
PR #16 (or new PR if needed)
