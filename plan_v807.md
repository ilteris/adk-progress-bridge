# Plan v807 - Supreme Apex Milestone 1240

## Objective
Reach 1240+ unique tools milestone. Increment version to 2.12.30. Add 32 new high-fidelity ultimate audit tools (V4 for process CPU and refined metrics). Verify via WebSocket.

## Proposed Changes
1. Update `backend/app/main.py`: Set `APP_VERSION = "2.12.30"`, `GIT_COMMIT = "v807-supreme-apex-1240-v1"`, `OPERATIONAL_APEX = "v807 SUPREME APEX 1240 VERIFICATION V1"`.
2. Update `backend/app/dummy_tool.py`: Add 32 new high-fidelity ultimate audit tools (V4):
    - `system_process_cpu_times_user_{avg,max,min,sum}_v4`
    - `system_process_cpu_times_system_{avg,max,min,sum}_v4`
    - `system_process_cpu_times_children_user_{avg,max,min,sum}_v4`
    - `system_process_cpu_times_children_system_{avg,max,min,sum}_v4`
    - `system_process_cpu_percent_{avg,max,min,sum}_v4`
    - `system_process_memory_percent_{avg,max,min,sum}_v4`
    - `system_process_num_threads_sum_v4`
    - `system_process_num_fds_sum_v4`
    - `system_process_cpu_affinity_count_sum_v4`
    - `system_process_children_count_sum_v4`
    - `system_process_memory_full_info_uss_sum_v4`
    - `system_process_memory_full_info_pss_sum_v4`
    - `system_process_memory_full_info_swap_sum_v4`
    - `system_process_ctx_switches_voluntary_sum_v4`
3. Update `frontend/tests/e2e/websocket.test.ts`: Update expected tool count to 1240.
4. Create `verify_v807.py` for testing via WebSocket.

## Verification Plan
1. Create `verify_v807.py` to test a subset of the new tools via the WebSocket API.
2. Restart the backend.
3. Execute `python3 verify_v807.py`.
4. Update `TODO.md` and `tasks/websocket-integration.json`.
