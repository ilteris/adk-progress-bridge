# Plan v640: SUPREME APEX VERIFICATION

## Goal
Implement three additional system audit tools to enhance the monitoring capabilities of the adk-progress-bridge.

## Tools to be added
1. `system_net_if_addrs_netmask_audit`: Audits network interface netmasks.
2. `system_disk_partitions_mountpoint_audit`: Audits disk partitions filtered by mountpoint.
3. `system_cpu_times_percent_user_focused_audit`: Audits system-wide user CPU time percentage.

## Steps
1. **Understand**: Review existing `psutil` tool implementations in `backend/app/dummy_tool.py`.
2. **Implement**: Add the new tools to `backend/app/dummy_tool.py`.
3. **Verify**:
    - Run existing tests to ensure no regressions.
    - Create a new verification script `verify_v640.py` to test the new tools.
    - Run the verification script.
4. **Finalize**:
    - Update `plan.md` with v640 completion.
    - Update `tasks/websocket-integration.json` history and status.
    - Create a Pull Request (using `gh pr create` if possible, but I'll check if I have `gh` tool).
    - Create an audit report `tasks/websocket_audit_report_feb01_final_signoff_verified_adele_v640.md`.
