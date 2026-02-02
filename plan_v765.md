# Plan v765 - Supreme Apex Verification

## Goal
Reach 600 unique tools milestone by adding 10 new high-fidelity audit tools for Disk Usage and Battery metrics. Increment version to 2.10.91.

## Steps
1. Add 10 new ultimate audit tools to `backend/app/dummy_tool.py`.
2. Update `backend/app/main.py` version to `2.10.91` and `GIT_COMMIT` to `v765-supreme-apex-adele-verification`.
3. Create `verify_v765.py` to test the new tools.
4. Run the verification script.
5. Update `TODO.md`.
6. Generate the final audit report `tasks/websocket_audit_report_feb02_final_signoff_verified_adele_v765.md`.
7. Update `inboxes/supervisor.jsonl` with completion status.

## New Tools
1. `system_disk_usage_total_avg_ultimate_audit`
2. `system_disk_usage_used_avg_ultimate_audit`
3. `system_disk_usage_free_avg_ultimate_audit`
4. `system_disk_usage_percent_avg_ultimate_audit`
5. `system_sensors_battery_percent_avg_ultimate_audit`
6. `system_sensors_battery_secsleft_avg_ultimate_audit`
7. `system_sensors_battery_secsleft_min_ultimate_audit`
8. `system_sensors_battery_secsleft_max_ultimate_audit`
9. `system_sensors_battery_power_plugged_avg_ultimate_audit`
10. `system_sensors_battery_power_plugged_max_ultimate_audit`
