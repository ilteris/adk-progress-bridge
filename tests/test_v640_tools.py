import pytest
from backend.app.dummy_tool import system_net_if_addrs_netmask_audit, system_disk_partitions_mountpoint_audit, system_cpu_times_percent_user_focused_audit
from backend.app.bridge import ProgressPayload

@pytest.mark.asyncio
async def test_system_net_if_addrs_netmask_audit():
    gen = system_net_if_addrs_netmask_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing netmask net if addrs probe"
    
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
    assert res["family"] == "netmask"

@pytest.mark.asyncio
async def test_system_disk_partitions_mountpoint_audit():
    gen = system_disk_partitions_mountpoint_audit(samples=1, mountpoint="/")
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing mountpoint-partitions probe"
    
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
    assert res["mountpoint"] == "/"

@pytest.mark.asyncio
async def test_system_cpu_times_percent_user_focused_audit():
    gen = system_cpu_times_percent_user_focused_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing user CPU focused probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "user_percent" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "final_user_percent" in res
    assert res["metric"] == "user_cpu_time"
