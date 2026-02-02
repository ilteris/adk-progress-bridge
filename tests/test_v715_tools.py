import pytest
from backend.app.dummy_tool import (
    system_memory_shared_ultimate_audit,
    system_memory_buffers_ultimate_audit,
    system_memory_cached_ultimate_audit
)

@pytest.mark.asyncio
async def test_system_memory_shared_ultimate_audit():
    gen = system_memory_shared_ultimate_audit(samples=1)
    results = []
    async for item in gen:
        results.append(item)
    assert len(results) >= 2
    assert results[-1]["status"] == "audit_complete"

@pytest.mark.asyncio
async def test_system_memory_buffers_ultimate_audit():
    gen = system_memory_buffers_ultimate_audit(samples=1)
    results = []
    async for item in gen:
        results.append(item)
    assert len(results) >= 2
    assert results[-1]["status"] == "audit_complete"

@pytest.mark.asyncio
async def test_system_memory_cached_ultimate_audit():
    gen = system_memory_cached_ultimate_audit(samples=1)
    results = []
    async for item in gen:
        results.append(item)
    assert len(results) >= 2
    assert results[-1]["status"] == "audit_complete"
