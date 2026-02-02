import pytest
import asyncio
from backend.app.dummy_tool import (
    system_net_io_packets_total_avg_audit,
    system_net_io_throughput_total_avg_audit,
    system_cpu_stats_total_avg_audit
)

@pytest.mark.asyncio
async def test_system_net_io_packets_total_avg_audit():
    gen = system_net_io_packets_total_avg_audit(samples=1)
    payloads = []
    async for p in gen:
        payloads.append(p)
    
    assert len(payloads) >= 2
    assert payloads[-1]["status"] == "audit_complete"
    assert "avg_net_packets_total" in payloads[-1]

@pytest.mark.asyncio
async def test_system_net_io_throughput_total_avg_audit():
    gen = system_net_io_throughput_total_avg_audit(samples=1)
    payloads = []
    async for p in gen:
        payloads.append(p)
    
    assert len(payloads) >= 2
    assert payloads[-1]["status"] == "audit_complete"
    assert "avg_net_throughput_total" in payloads[-1]

@pytest.mark.asyncio
async def test_system_cpu_stats_total_avg_audit():
    gen = system_cpu_stats_total_avg_audit(samples=1)
    payloads = []
    async for p in gen:
        payloads.append(p)
    
    assert len(payloads) >= 2
    assert payloads[-1]["status"] == "audit_complete"
    assert "avg_cpu_stats_total" in payloads[-1]
