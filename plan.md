# Implementation Plan - WebSocket Integration Robustness

## Problem
WebSocket-started tasks are currently not marked as "consumed" in the `ToolRegistry`. This makes them vulnerable to being prematurely terminated by the background `cleanup_stale_tasks` loop if they run longer than the stale threshold (default 300s).

## Proposed Changes

### 1. Backend (bridge.py)
- Add `mark_consumed(call_id: str)` method to `ToolRegistry` to allow explicit state updates without retrieving the generator (since WS flow already has it).

### 2. Backend (main.py)
- Call `registry.mark_consumed(call_id)` in the WebSocket `start` message handler after storing the task.

### 3. Documentation (rules.md)
- Update `rules.md` to include WebSocket specifications, matching the SSE standards.

## Verification Plan
- Run `tests/test_websocket.py` to ensure no regressions.
- Add a specific test case in a new test file `tests/test_ws_cleanup.py` that verifies WS tasks are NOT reaped by the stale cleanup loop.
