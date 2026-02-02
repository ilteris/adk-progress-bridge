import pytest
import asyncio
from backend.app.dummy_tool import (
    system_cpu_times_softirq_avg_audit,
    system_cpu_times_steal_avg_audit,
    system_cpu_times_guest_avg_audit
)
from backend.app.bridge import ProgressPayload

@pytest.mark.asyncio
async def test_system_cpu_times_softirq_avg_audit():
    gen = system_cpu_times_softirq_avg_audit(samples=1)
    results = []
    async for item in gen:
        results.append(item)
    
    assert len(results) >= 2
    assert isinstance(results[0], ProgressPayload)
    assert results[-1]["status"] == "audit_complete"
    assert "avg_cpu_softirq_time" in results[-1]

@pytest.mark.asyncio
async def test_system_cpu_times_steal_avg_audit():
    gen = system_cpu_times_steal_avg_audit(samples=1)
    results = []
    async for item in gen:
        results.append(item)
    
    assert len(results) >= 2
    assert isinstance(results[0], ProgressPayload)
    assert results[-1]["status"] == "audit_complete"
    assert "avg_cpu_steal_time" in results[-1]

@pytest.mark.asyncio
async def test_system_cpu_times_guest_avg_audit():
    gen = system_cpu_times_guest_avg_audit(samples=1)
    results = []
    async for item in gen:
        results.append(item)
    
    assert len(results) >= 2
    assert isinstance(results[0], ProgressPayload)
    assert results[-1]["status"] == "audit_complete"
    assert "avg_cpu_guest_time" in results[-1]
