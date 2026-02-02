import pytest
import asyncio
from backend.app.dummy_tool import (
    system_net_io_sent_bytes_avg_audit,
    system_net_io_recv_bytes_avg_audit,
    system_net_io_packets_sent_avg_audit
)
from backend.app.bridge import ProgressPayload

@pytest.mark.asyncio
async def test_system_net_io_sent_bytes_avg_audit():
    gen = system_net_io_sent_bytes_avg_audit(samples=1)
    results = []
    async for item in gen:
        results.append(item)
    
    assert len(results) >= 2
    assert isinstance(results[0], ProgressPayload)
    assert results[-1]["status"] == "audit_complete"
    assert "avg_net_sent_bytes" in results[-1]

@pytest.mark.asyncio
async def test_system_net_io_recv_bytes_avg_audit():
    gen = system_net_io_recv_bytes_avg_audit(samples=1)
    results = []
    async for item in gen:
        results.append(item)
    
    assert len(results) >= 2
    assert isinstance(results[0], ProgressPayload)
    assert results[-1]["status"] == "audit_complete"
    assert "avg_net_recv_bytes" in results[-1]

@pytest.mark.asyncio
async def test_system_net_io_packets_sent_avg_audit():
    gen = system_net_io_packets_sent_avg_audit(samples=1)
    results = []
    async for item in gen:
        results.append(item)
    
    assert len(results) >= 2
    assert isinstance(results[0], ProgressPayload)
    assert results[-1]["status"] == "audit_complete"
    assert "avg_net_packets_sent" in results[-1]
