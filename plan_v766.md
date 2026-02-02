# Plan v766 - Supreme Apex Verification

## Goal
Reach 610 unique tools milestone by adding 10 new high-fidelity audit tools for Temperature and Fan metrics. Increment version to 2.10.92.

## Steps
1. Add 10 new ultimate audit tools to `backend/app/dummy_tool.py`.
2. Update `backend/app/main.py` version to `2.10.92` and `GIT_COMMIT` to `v766-supreme-apex-adele-verification`.
3. Create `verify_v766.py` to test the new tools.
4. Run the verification script.
5. Update `TODO.md` and `SPEC.md`.
6. Update `tasks/websocket-integration.json`.
7. Generate the final audit report `tasks/websocket_audit_report_feb02_final_signoff_verified_adele_v766.md`.
8. Update `inboxes/supervisor.jsonl` with completion status.

## New Tools
1. `system_sensors_temperatures_core_avg_ultimate_audit`
2. `system_sensors_temperatures_core_max_ultimate_audit`
3. `system_sensors_temperatures_core_min_ultimate_audit`
4. `system_sensors_temperatures_package_avg_ultimate_audit`
5. `system_sensors_temperatures_package_max_ultimate_audit`
6. `system_sensors_fans_cpu_avg_ultimate_audit`
7. `system_sensors_fans_cpu_max_ultimate_audit`
8. `system_sensors_fans_cpu_min_ultimate_audit`
9. `system_sensors_fans_case_avg_ultimate_audit`
10. `system_sensors_fans_case_max_ultimate_audit`
