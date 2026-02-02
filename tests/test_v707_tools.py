import pytest
import asyncio
from backend.app.dummy_tool import system_disk_io_write_bytes_ultimate_audit, system_disk_io_read_time_ultimate_audit, system_disk_io_write_time_ultimate_audit
from backend.app.bridge import ProgressPayload

@pytest.mark.asyncio
async def test_system_disk_io_write_bytes_ultimate_audit():
    gen = system_disk_io_write_bytes_ultimate_audit(samples=1)
    payloads = []
    async for p in gen:
        payloads.append(p)
    
    assert len(payloads) >= 2
    assert any(isinstance(p, ProgressPayload) for p in payloads)
    assert any(isinstance(p, dict) and p.get("status") == "audit_complete" for p in payloads)
    
    final_result = payloads[-1]
    assert "avg_write_bytes" in final_result

@pytest.mark.asyncio
async def test_system_disk_io_read_time_ultimate_audit():
    gen = system_disk_io_read_time_ultimate_audit(samples=1)
    payloads = []
    async for p in gen:
        payloads.append(p)
    
    assert len(payloads) >= 2
    assert any(isinstance(p, ProgressPayload) for p in payloads)
    assert any(isinstance(p, dict) and p.get("status") == "audit_complete" for p in payloads)
    
    final_result = payloads[-1]
    assert "avg_read_time" in final_result

@pytest.mark.asyncio
async def test_system_disk_io_write_time_ultimate_audit():
    gen = system_disk_io_write_time_ultimate_audit(samples=1)
    payloads = []
    async for p in gen:
        payloads.append(p)
    
    assert len(payloads) >= 2
    assert any(isinstance(p, ProgressPayload) for p in payloads)
    assert any(isinstance(p, dict) and p.get("status") == "audit_complete" for p in payloads)
    
    final_result = payloads[-1]
    assert "avg_write_time" in final_result
