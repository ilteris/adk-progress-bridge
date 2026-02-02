# Plan v791 - Supreme Apex Verification

## Objective
Reach 860+ unique tools milestone. Increment version to 2.12.14. Verify via WebSocket.

## Proposed Changes
1. Update `backend/app/main.py`: Set `APP_VERSION = "2.12.14"`, `GIT_COMMIT = "v791-supreme-apex-proc-extended-v6"`, `OPERATIONAL_APEX = "v791 SUPREME APEX VERIFICATION PROCESS EXTENDED V6"`.
2. Update `backend/app/dummy_tool.py`: Add 10 new high-fidelity ultimate audit tools for process metrics (open files, threads, context switches).
   - `system_process_open_files_count_avg_ultimate_audit`
   - `system_process_open_files_count_max_ultimate_audit`
   - `system_process_open_files_count_min_ultimate_audit`
   - `system_process_threads_count_avg_ultimate_audit`
   - `system_process_threads_count_max_ultimate_audit`
   - `system_process_threads_count_min_ultimate_audit`
   - `system_process_num_ctx_switches_voluntary_avg_ultimate_audit`
   - `system_process_num_ctx_switches_voluntary_max_ultimate_audit`
   - `system_process_num_ctx_switches_involuntary_avg_ultimate_audit`
   - `system_process_num_ctx_switches_involuntary_max_ultimate_audit`

## Verification Plan
1. Create `verify_v791.py` to test the new tools via the WebSocket API.
2. Start the backend: `venv/bin/python -m backend.app.main`
3. Execute `venv/bin/python verify_v791.py`.
4. Update `TODO.md` and `tasks/websocket-integration.json`.
5. Generate `tasks/websocket_audit_report_feb02_final_signoff_verified_adele_v791.md`.
