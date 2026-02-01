import pytest
from backend.app.dummy_tool import system_boot_time_audit, system_cpu_freq_audit, system_cpu_stats_audit

@pytest.mark.asyncio
async def test_system_boot_time_audit():
    gen = system_boot_time_audit(samples=1)
    items = []
    async for item in gen:
        items.append(item)
    assert len(items) >= 2
    assert items[-1]["status"] == "audit_complete"

@pytest.mark.asyncio
async def test_system_cpu_freq_audit():
    gen = system_cpu_freq_audit(samples=1)
    items = []
    async for item in gen:
        items.append(item)
    assert len(items) >= 2
    assert items[-1]["status"] == "audit_complete"

@pytest.mark.asyncio
async def test_system_cpu_stats_audit():
    gen = system_cpu_stats_audit(samples=1)
    items = []
    async for item in gen:
        items.append(item)
    assert len(items) >= 2
    assert items[-1]["status"] == "audit_complete"
