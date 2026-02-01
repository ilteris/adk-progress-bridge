# Plan v646: SUPREME APEX VERIFICATION

## Goal
Implement three additional system audit tools to enhance the monitoring capabilities of the adk-progress-bridge.

## Tools to be added
1. `system_cpu_times_percent_nice_focused_audit`: Audits system-wide nice CPU time percentage.
2. `system_disk_io_read_count_audit`: Audits system-wide disk read operations count.
3. `system_disk_io_write_count_audit`: Audits system-wide disk write operations count.

## Steps
1. **Understand**: Review existing `psutil` tool implementations in `backend/app/dummy_tool.py`.
2. **Implement**: Add the new tools to `backend/app/dummy_tool.py`.
3. **Verify**:
    - Run existing tests to ensure no regressions.
    - Create a new pytest file `tests/test_v646_tools.py`.
    - Run all tests (255 total expected).
4. **Finalize**:
    - Update `plan.md` with v646 completion.
    - Update `tasks/websocket-integration.json` history and status.
    - Create an audit report `tasks/websocket_audit_report_feb01_final_signoff_verified_adele_v646.md`.
