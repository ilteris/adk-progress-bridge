# Plan v641: SUPREME APEX VERIFICATION

## Goal
Implement three additional system audit tools to enhance the monitoring capabilities of the adk-progress-bridge.

## Tools to be added
1. `system_net_if_addrs_broadcast_audit`: Audits network interface broadcast addresses.
2. `system_disk_partitions_device_audit`: Audits disk partitions filtered by device name.
3. `system_cpu_times_percent_idle_focused_audit`: Audits system-wide idle CPU time percentage.

## Steps
1. **Understand**: Review existing `psutil` tool implementations in `backend/app/dummy_tool.py`.
2. **Implement**: Add the new tools to `backend/app/dummy_tool.py`.
3. **Verify**:
    - Run existing tests to ensure no regressions.
    - Create new pytest files `tests/test_v640_tools.py` and `tests/test_v641_tools.py`.
    - Run all tests (240 total).
4. **Finalize**:
    - Update `plan.md` with v641 completion.
    - Update `tasks/websocket-integration.json` history and status.
    - Create an audit report `tasks/websocket_audit_report_feb01_final_signoff_verified_adele_v641.md`.
