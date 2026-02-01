# Plan v644: SUPREME APEX VERIFICATION

## Goal
Implement three additional system audit tools to enhance the monitoring capabilities of the adk-progress-bridge.

## Tools to be added
1. `system_cpu_times_percent_steal_focused_audit`: Audits system-wide steal CPU time percentage.
2. `system_cpu_times_percent_guest_focused_audit`: Audits system-wide guest CPU time percentage.
3. `system_disk_partitions_limits_audit`: Audits maxfile and maxpath limits for partitions.

## Steps
1. **Understand**: Review existing `psutil` tool implementations in `backend/app/dummy_tool.py`.
2. **Implement**: Add the new tools to `backend/app/dummy_tool.py`.
3. **Verify**:
    - Run existing tests to ensure no regressions.
    - Create a new pytest file `tests/test_v644_tools.py`.
    - Run all tests (249 total expected).
4. **Finalize**:
    - Update `plan.md` with v644 completion.
    - Update `tasks/websocket-integration.json` history and status.
    - Create an audit report `tasks/websocket_audit_report_feb01_final_signoff_verified_adele_v644.md`.
