import pytest
from backend.app.dummy_tool import system_net_if_addrs_broadcast_audit, system_disk_partitions_device_audit, system_cpu_times_percent_idle_focused_audit
from backend.app.bridge import ProgressPayload
import psutil

@pytest.mark.asyncio
async def test_system_net_if_addrs_broadcast_audit():
    gen = system_net_if_addrs_broadcast_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing broadcast net if addrs probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert isinstance(p2.metadata, dict)
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    assert isinstance(p3, ProgressPayload)
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "interface_count" in res
    assert res["family"] == "broadcast"

@pytest.mark.asyncio
async def test_system_disk_partitions_device_audit():
    # Get a real device name if possible, or just use what we have
    partitions = psutil.disk_partitions(all=True)
    device = partitions[0].device if partitions else "/dev/disk1s1"
    
    gen = system_disk_partitions_device_audit(samples=1, device=device)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing device-partitions probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert isinstance(p2.metadata, dict)
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "partition_count" in res
    assert res["device"] == device

@pytest.mark.asyncio
async def test_system_cpu_times_percent_idle_focused_audit():
    gen = system_cpu_times_percent_idle_focused_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing idle CPU focused probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "idle_percent" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "final_idle_percent" in res
    assert res["metric"] == "idle_cpu_time"
