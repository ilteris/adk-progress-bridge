import pytest
from backend.app.dummy_tool import system_sensors_temperatures_audit, system_sensors_fans_audit, system_sensors_battery_audit

@pytest.mark.asyncio
async def test_system_sensors_temperatures_audit():
    gen = system_sensors_temperatures_audit(samples=1)
    items = []
    async for item in gen:
        items.append(item)
    assert len(items) >= 2
    assert items[-1]["status"] == "audit_complete"

@pytest.mark.asyncio
async def test_system_sensors_fans_audit():
    gen = system_sensors_fans_audit(samples=1)
    items = []
    async for item in gen:
        items.append(item)
    assert len(items) >= 2
    assert items[-1]["status"] == "audit_complete"

@pytest.mark.asyncio
async def test_system_sensors_battery_audit():
    gen = system_sensors_battery_audit(samples=1)
    items = []
    async for item in gen:
        items.append(item)
    assert len(items) >= 2
    assert items[-1]["status"] == "audit_complete"
