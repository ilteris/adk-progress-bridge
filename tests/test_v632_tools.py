import pytest
from backend.app.dummy_tool import system_cpu_count_audit, system_cpu_times_percent_audit, system_net_connections_audit

@pytest.mark.asyncio
async def test_system_cpu_count_audit():
    gen = system_cpu_count_audit(samples=1)
    items = []
    async for item in gen:
        items.append(item)
    assert len(items) >= 2
    assert items[-1]["status"] == "audit_complete"
    assert "logical" in items[-1]
    assert "physical" in items[-1]

@pytest.mark.asyncio
async def test_system_cpu_times_percent_audit():
    gen = system_cpu_times_percent_audit(samples=1)
    items = []
    async for item in gen:
        items.append(item)
    assert len(items) >= 2
    assert items[-1]["status"] == "audit_complete"
    assert "final_cpu_times_percent" in items[-1]

@pytest.mark.asyncio
async def test_system_net_connections_audit():
    gen = system_net_connections_audit(samples=1)
    items = []
    async for item in gen:
        items.append(item)
    assert len(items) >= 2
    assert items[-1]["status"] == "audit_complete"
    assert "final_connections_count" in items[-1]
