import pytest
from backend.app.dummy_tool import (
    system_swap_memory_total_ultimate_audit,
    system_swap_memory_used_ultimate_audit,
    system_swap_memory_free_ultimate_audit
)

@pytest.mark.asyncio
async def test_system_swap_memory_total_ultimate_audit():
    gen = system_swap_memory_total_ultimate_audit(samples=1)
    results = []
    async for item in gen:
        results.append(item)
    assert len(results) >= 2
    assert results[-1]["status"] == "audit_complete"

@pytest.mark.asyncio
async def test_system_swap_memory_used_ultimate_audit():
    gen = system_swap_memory_used_ultimate_audit(samples=1)
    results = []
    async for item in gen:
        results.append(item)
    assert len(results) >= 2
    assert results[-1]["status"] == "audit_complete"

@pytest.mark.asyncio
async def test_system_swap_memory_free_ultimate_audit():
    gen = system_swap_memory_free_ultimate_audit(samples=1)
    results = []
    async for item in gen:
        results.append(item)
    assert len(results) >= 2
    assert results[-1]["status"] == "audit_complete"
