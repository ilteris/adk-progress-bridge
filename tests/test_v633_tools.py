import pytest
import asyncio
from backend.app.dummy_tool import system_pids_audit, system_cpu_times_audit, system_disk_io_counters_audit
from backend.app.bridge import ProgressPayload

@pytest.mark.asyncio
async def test_system_pids_audit():
    gen = system_pids_audit(samples=1)
    async for item in gen:
        if isinstance(item, ProgressPayload):
            assert item.step in ["Initializing PID list probe", "Sampling system PIDs", "Finalizing"]
            if item.step == "Sampling system PIDs":
                assert "count" in item.metadata
        else:
            assert item["status"] == "audit_complete"
            assert "final_pid_count" in item

@pytest.mark.asyncio
async def test_system_cpu_times_audit():
    gen = system_cpu_times_audit(samples=1)
    async for item in gen:
        if isinstance(item, ProgressPayload):
            assert item.step in ["Initializing CPU times probe", "Sampling CPU times", "Finalizing"]
            if item.step == "Sampling CPU times":
                assert "user" in item.metadata
        else:
            assert item["status"] == "audit_complete"
            assert "final_cpu_times" in item

@pytest.mark.asyncio
async def test_system_disk_io_counters_audit():
    gen = system_disk_io_counters_audit(samples=1)
    async for item in gen:
        if isinstance(item, ProgressPayload):
            assert item.step in ["Initializing disk I/O probe", "Sampling disk I/O", "Finalizing"]
            if item.step == "Sampling disk I/O":
                assert "read_bytes" in item.metadata
        else:
            assert item["status"] == "audit_complete"
            assert "final_counters" in item
