# Plan v645: SUPREME APEX VERIFICATION

## Goal
Implement three additional system audit tools to enhance the monitoring capabilities of the adk-progress-bridge.

## Tools to be added
1. `system_cpu_times_percent_guest_nice_focused_audit`: Audits system-wide guest_nice CPU time percentage.
2. `system_net_io_packets_audit`: Audits system-wide network packets sent and received.
3. `system_disk_io_time_audit`: Audits system-wide disk I/O time.

## Steps
1. **Understand**: Review existing `psutil` tool implementations in `backend/app/dummy_tool.py`.
2. **Implement**: Add the new tools to `backend/app/dummy_tool.py`.
3. **Verify**:
    - Run existing tests to ensure no regressions.
    - Create a new pytest file `tests/test_v645_tools.py`.
    - Run all tests (252 total expected).
4. **Finalize**:
    - Update `plan.md` with v645 completion.
    - Update `tasks/websocket-integration.json` history and status.
    - Create an audit report `tasks/websocket_audit_report_feb01_final_signoff_verified_adele_v645.md`.
