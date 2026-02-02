# Plan v764 - Supreme Apex Verification

## Goal
Reach 590 unique tools milestone by adding 10 new high-fidelity "min/max" audit tools for Disk Usage and Battery. Increment version to 2.10.90.

## Steps
1. Add 10 new "min/max" ultimate audit tools to `backend/app/dummy_tool.py`.
2. Update `backend/app/main.py` version to `2.10.90` and `GIT_COMMIT` to `v764-supreme-apex-adele-verification`.
3. Create `verify_v764.py` to test the new tools.
4. Run the verification script.
5. Update `TODO.md`.
6. Generate the final audit report `tasks/websocket_audit_report_feb02_final_signoff_verified_adele_v764.md`.
7. Update `inboxes/supervisor.jsonl` with completion status.

## New Tools
1. `system_disk_usage_total_max_ultimate_audit`
2. `system_disk_usage_used_max_ultimate_audit`
3. `system_disk_usage_free_max_ultimate_audit`
4. `system_disk_usage_percent_max_ultimate_audit`
5. `system_disk_usage_total_min_ultimate_audit`
6. `system_disk_usage_used_min_ultimate_audit`
7. `system_disk_usage_free_min_ultimate_audit`
8. `system_disk_usage_percent_min_ultimate_audit`
9. `system_sensors_battery_percent_max_ultimate_audit`
10. `system_sensors_battery_percent_min_ultimate_audit`
