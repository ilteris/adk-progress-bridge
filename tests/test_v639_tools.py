import pytest
from backend.app.dummy_tool import system_net_if_addrs_mac_audit, system_disk_partitions_fstype_audit, system_cpu_times_percent_system_focused_audit
from backend.app.bridge import ProgressPayload

@pytest.mark.asyncio
async def test_system_net_if_addrs_mac_audit():
    gen = system_net_if_addrs_mac_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing MAC net if addrs probe"
    
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
    assert res["family"] == "MAC"

@pytest.mark.asyncio
async def test_system_disk_partitions_fstype_audit():
    # Try with a common fstype
    gen = system_disk_partitions_fstype_audit(samples=1, fstype="apfs")
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing fstype-partitions probe"
    
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
    assert res["fstype"] == "apfs"

@pytest.mark.asyncio
async def test_system_cpu_times_percent_system_focused_audit():
    gen = system_cpu_times_percent_system_focused_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing system CPU focused probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "system_percent" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "final_system_percent" in res
    assert res["metric"] == "system_cpu_time"
