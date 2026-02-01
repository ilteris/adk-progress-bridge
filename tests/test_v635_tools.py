import pytest
import asyncio
import psutil
from backend.app.dummy_tool import system_net_io_per_nic_audit, system_disk_io_per_disk_audit, system_cpu_times_per_cpu_audit
from backend.app.bridge import ProgressPayload

@pytest.mark.asyncio
async def test_system_net_io_per_nic_audit():
    gen = system_net_io_per_nic_audit(samples=1)
    async for item in gen:
        if isinstance(item, ProgressPayload):
            assert item.step in ["Initializing per-NIC probe", "Sampling per-NIC I/O", "Finalizing"]
            if item.step == "Sampling per-NIC I/O":
                if "error" not in item.metadata:
                    # Should contain NIC names
                    assert len(item.metadata) > 0
        else:
            assert item["status"] == "audit_complete"
            assert "interface_count" in item

@pytest.mark.asyncio
async def test_system_disk_io_per_disk_audit():
    gen = system_disk_io_per_disk_audit(samples=1)
    async for item in gen:
        if isinstance(item, ProgressPayload):
            assert item.step in ["Initializing per-disk probe", "Sampling per-disk I/O", "Finalizing"]
            if item.step == "Sampling per-disk I/O":
                if "error" not in item.metadata:
                    # Might be empty if no disk I/O counters available (e.g. in some CI environments)
                    pass
        else:
            assert item["status"] == "audit_complete"
            assert "disk_count" in item

@pytest.mark.asyncio
async def test_system_cpu_times_per_cpu_audit():
    gen = system_cpu_times_per_cpu_audit(samples=1)
    async for item in gen:
        if isinstance(item, ProgressPayload):
            assert item.step in ["Initializing per-CPU probe", "Sampling per-CPU timings", "Finalizing"]
            if item.step == "Sampling per-CPU timings":
                if "error" not in item.metadata:
                    assert "cpu_0" in item.metadata
        else:
            assert item["status"] == "audit_complete"
            assert "cpu_count" in item
