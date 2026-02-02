# Plan v790 - Supreme Apex Verification

## Objective
Reach 840+ unique tools milestone. Increment version to 2.12.13. Verify via WebSocket.

## Proposed Changes
1. Update `backend/app/main.py`: Set `APP_VERSION = "2.12.13"`, `GIT_COMMIT = "v790-supreme-apex-proc-mem-extended-v5"`, `OPERATIONAL_APEX = "v790 SUPREME APEX VERIFICATION PROCESS MEM EXTENDED V5"`.
2. Update `backend/app/dummy_tool.py`: Add 11 new high-fidelity ultimate audit tools for process memory info (dirty max/min, uss, pss, swap).
   - `system_process_memory_info_dirty_max_ultimate_audit`
   - `system_process_memory_info_dirty_min_ultimate_audit`
   - `system_process_memory_info_uss_avg_ultimate_audit`
   - `system_process_memory_info_uss_max_ultimate_audit`
   - `system_process_memory_info_uss_min_ultimate_audit`
   - `system_process_memory_info_pss_avg_ultimate_audit`
   - `system_process_memory_info_pss_max_ultimate_audit`
   - `system_process_memory_info_pss_min_ultimate_audit`
   - `system_process_memory_info_swap_avg_ultimate_audit`
   - `system_process_memory_info_swap_max_ultimate_audit`
   - `system_process_memory_info_swap_min_ultimate_audit`

## Verification Plan
1. Create `verify_v790.py` to test the new tools via the WebSocket API.
2. Execute `venv/bin/python verify_v790.py`.
3. Update `TODO.md` and `tasks/websocket-integration.json`.
4. Generate `tasks/websocket_audit_report_feb02_final_signoff_verified_adele_v790.md`.
