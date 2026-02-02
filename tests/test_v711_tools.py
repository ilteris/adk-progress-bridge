import pytest
from backend.app.dummy_tool import (
    system_cpu_stats_ctx_switches_ultimate_audit,
    system_cpu_stats_interrupts_ultimate_audit,
    system_cpu_stats_soft_interrupts_ultimate_audit
)
from backend.app.bridge import ProgressPayload

@pytest.mark.asyncio
async def test_system_cpu_stats_ctx_switches_ultimate_audit():
    gen = system_cpu_stats_ctx_switches_ultimate_audit(samples=1)
    results = []
    async for p in gen:
        results.append(p)
    assert len(results) >= 3
    assert any(isinstance(r, dict) and r["status"] == "audit_complete" for r in results)

@pytest.mark.asyncio
async def test_system_cpu_stats_interrupts_ultimate_audit():
    gen = system_cpu_stats_interrupts_ultimate_audit(samples=1)
    results = []
    async for p in gen:
        results.append(p)
    assert len(results) >= 3
    assert any(isinstance(r, dict) and r["status"] == "audit_complete" for r in results)

@pytest.mark.asyncio
async def test_system_cpu_stats_soft_interrupts_ultimate_audit():
    gen = system_cpu_stats_soft_interrupts_ultimate_audit(samples=1)
    results = []
    async for p in gen:
        results.append(p)
    assert len(results) >= 3
    assert any(isinstance(r, dict) and r["status"] == "audit_complete" for r in results)
