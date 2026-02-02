import pytest
from backend.app.dummy_tool import (
    system_net_io_dropin_ultimate_audit,
    system_net_io_dropout_ultimate_audit,
    system_disk_io_read_count_ultimate_audit
)
from backend.app.bridge import ProgressPayload

@pytest.mark.asyncio
async def test_system_net_io_dropin_ultimate_audit():
    gen = system_net_io_dropin_ultimate_audit(samples=1)
    results = []
    async for p in gen:
        results.append(p)
    assert len(results) >= 3
    assert any(isinstance(r, dict) and r["status"] == "audit_complete" for r in results)

@pytest.mark.asyncio
async def test_system_net_io_dropout_ultimate_audit():
    gen = system_net_io_dropout_ultimate_audit(samples=1)
    results = []
    async for p in gen:
        results.append(p)
    assert len(results) >= 3
    assert any(isinstance(r, dict) and r["status"] == "audit_complete" for r in results)

@pytest.mark.asyncio
async def test_system_disk_io_read_count_ultimate_audit():
    gen = system_disk_io_read_count_ultimate_audit(samples=1)
    results = []
    async for p in gen:
        results.append(p)
    assert len(results) >= 3
    assert any(isinstance(r, dict) and r["status"] == "audit_complete" for r in results)
