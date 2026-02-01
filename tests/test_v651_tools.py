import pytest
import asyncio
from backend.app.dummy_tool import system_disk_io_write_bytes_audit, system_net_io_sent_bytes_audit, system_net_io_recv_bytes_audit

@pytest.mark.asyncio
async def test_system_disk_io_write_bytes_audit():
    gen = system_disk_io_write_bytes_audit(samples=1)
    results = []
    async for msg in gen:
        results.append(msg)
    
    assert len(results) >= 2
    final_result = results[-1]
    assert final_result["status"] == "audit_complete"
    assert "final_write_bytes" in final_result

@pytest.mark.asyncio
async def test_system_net_io_sent_bytes_audit():
    gen = system_net_io_sent_bytes_audit(samples=1)
    results = []
    async for msg in gen:
        results.append(msg)
    
    assert len(results) >= 2
    final_result = results[-1]
    assert final_result["status"] == "audit_complete"
    assert "final_bytes_sent" in final_result

@pytest.mark.asyncio
async def test_system_net_io_recv_bytes_audit():
    gen = system_net_io_recv_bytes_audit(samples=1)
    results = []
    async for msg in gen:
        results.append(msg)
    
    assert len(results) >= 2
    final_result = results[-1]
    assert final_result["status"] == "audit_complete"
    assert "final_bytes_recv" in final_result
