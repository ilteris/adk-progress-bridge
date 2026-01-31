# Implementation Plan - v399 Absolute Final Equilibrium

## 1. Version Synchronization
- Update `frontend/src/App.vue` version from 1.8.0 to 1.8.1 to match backend and SPEC.

## 2. SPEC & Code Alignment
- Update `SPEC.md` to reflect that `AgentState` uses `systemMetrics` instead of `health`.
- Ensure consistency in terminology across documentation.

## 3. WebSocket Buffer Optimization
- Refine `WebSocketManager.subscribe` in `useAgentStream.ts` to ensure broadcast messages like `system_metrics` are not prematurely cleared from the buffer if multiple subscribers exist.

## 4. Verification
- Run all 109 tests (88 backend, 16 frontend unit, 5 E2E).
- Verify the UI displays the correct version and metrics.

## 5. Final Sign-off
- Generate `tasks/websocket_audit_report_jan31_v399_absolute_final_equilibrium.md`.
- Update `tasks/websocket-integration.json`.