import pytest
import asyncio
from backend.app.dummy_tool import (
    system_memory_total_avg_audit,
    system_memory_used_percent_avg_audit,
    system_disk_io_total_avg_audit
)

@pytest.mark.asyncio
async def test_system_memory_total_avg_audit():
    gen = system_memory_total_avg_audit(samples=1)
    payloads = []
    async for p in gen:
        payloads.append(p)
    
    assert len(payloads) >= 2
    assert payloads[-1]["status"] == "audit_complete"
    assert "avg_memory_total" in payloads[-1]

@pytest.mark.asyncio
async def test_system_memory_used_percent_avg_audit():
    gen = system_memory_used_percent_avg_audit(samples=1)
    payloads = []
    async for p in gen:
        payloads.append(p)
    
    assert len(payloads) >= 2
    assert payloads[-1]["status"] == "audit_complete"
    assert "avg_memory_used_percent" in payloads[-1]

@pytest.mark.asyncio
async def test_system_disk_io_total_avg_audit():
    gen = system_disk_io_total_avg_audit(samples=1)
    payloads = []
    async for p in gen:
        payloads.append(p)
    
    assert len(payloads) >= 2
    assert payloads[-1]["status"] == "audit_complete"
    assert "avg_disk_io_total" in payloads[-1]
