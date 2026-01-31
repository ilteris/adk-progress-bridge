# Verification Plan - v306 (The Absolute Peak)

1. **Environment Audit**: Confirm all dependencies and environment variables are set.
2. **Backend Verification**: Run all 82 backend tests using pytest (includes binary frame handling and stress tests).
3. **Frontend Unit Verification**: Run all 16 Vitest tests (TaskMonitor and useAgentStream).
4. **E2E Verification**: Run all 5 Playwright E2E tests (Audit flow and WebSocket flows).
5. **Manual Smoke Test**: Execute `verify_websocket.py`, `backend/verify_docs.py`, and `verify_stream.py`.
6. **Documentation Audit**: Verify SPEC.md and rules.md are consistent with the latest implementation.
7. **Audit Report Generation**: Create `tasks/websocket_audit_report_jan31_final_v306.md`.
8. **Final Sign-off**: Update `tasks/websocket-integration.json` and create a PR.
