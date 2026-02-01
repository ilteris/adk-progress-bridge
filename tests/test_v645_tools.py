import pytest
from backend.app.dummy_tool import system_cpu_times_percent_guest_nice_focused_audit, system_net_io_packets_audit, system_disk_io_time_audit
from backend.app.bridge import ProgressPayload
import psutil

@pytest.mark.asyncio
async def test_system_cpu_times_percent_guest_nice_focused_audit():
    gen = system_cpu_times_percent_guest_nice_focused_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing guest_nice CPU focused probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "guest_nice_percent" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "final_guest_nice_percent" in res
    assert res["metric"] == "guest_nice_cpu_time"

@pytest.mark.asyncio
async def test_system_net_io_packets_audit():
    gen = system_net_io_packets_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing network packet probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "packets_sent" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "final_packets" in res

@pytest.mark.asyncio
async def test_system_disk_io_time_audit():
    gen = system_disk_io_time_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing disk I/O time probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "read_time_ms" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "final_io_time" in res
