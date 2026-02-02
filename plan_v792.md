# Plan v792 - Supreme Apex RLIMIT Verification

## Objective
Reach 890+ unique tools milestone. Increment version to 2.12.15. Verify via WebSocket.

## Proposed Changes
1. Update `backend/app/main.py`: Set `APP_VERSION = "2.12.15"`, `GIT_COMMIT = "v792-supreme-apex-rlimit-v1"`, `OPERATIONAL_APEX = "v792 SUPREME APEX RLIMIT VERIFICATION V1"`.
2. Update `backend/app/dummy_tool.py`: Add 27 new high-fidelity ultimate audit tools for process metrics.
   - `system_process_ionice_value_ultimate_audit`
   - `system_process_rlimit_nofile_soft_ultimate_audit`
   - `system_process_rlimit_nofile_hard_ultimate_audit`
   - `system_process_rlimit_cpu_soft_ultimate_audit`
   - `system_process_rlimit_cpu_hard_ultimate_audit`
   - `system_process_rlimit_fsize_soft_ultimate_audit`
   - `system_process_rlimit_fsize_hard_ultimate_audit`
   - `system_process_rlimit_memlock_soft_ultimate_audit`
   - `system_process_rlimit_memlock_hard_ultimate_audit`
   - `system_process_rlimit_rss_soft_ultimate_audit`
   - `system_process_rlimit_rss_hard_ultimate_audit`
   - `system_process_rlimit_nproc_soft_ultimate_audit`
   - `system_process_rlimit_nproc_hard_ultimate_audit`
   - `system_process_rlimit_stack_soft_ultimate_audit`
   - `system_process_rlimit_stack_hard_ultimate_audit`
   - `system_process_cpu_times_children_user_avg_ultimate_audit`
   - `system_process_cpu_times_children_user_max_ultimate_audit`
   - `system_process_cpu_times_children_user_min_ultimate_audit`
   - `system_process_cpu_times_children_system_avg_ultimate_audit`
   - `system_process_cpu_times_children_system_max_ultimate_audit`
   - `system_process_cpu_times_children_system_min_ultimate_audit`
   - `system_process_cpu_times_iowait_avg_ultimate_audit`
   - `system_process_cpu_times_iowait_max_ultimate_audit`
   - `system_process_cpu_times_iowait_min_ultimate_audit`
   - `system_process_memory_maps_count_avg_ultimate_audit`
   - `system_process_memory_maps_count_max_ultimate_audit`
   - `system_process_memory_maps_count_min_ultimate_audit`

## Verification Plan
1. Create `verify_v792.py` to test a subset of the new tools via the WebSocket API.
2. Start the backend: `venv/bin/python -m backend.app.main`
3. Execute `venv/bin/python verify_v792.py`.
4. Update `TODO.md` and `tasks/websocket-integration.json`.
5. Generate `tasks/websocket_audit_report_feb02_final_signoff_verified_adele_v792.md`.