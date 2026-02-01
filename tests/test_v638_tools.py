import pytest
from backend.app.dummy_tool import system_net_if_addrs_v4_audit, system_net_if_addrs_v6_audit, system_disk_partitions_physical_audit
from backend.app.bridge import ProgressPayload

@pytest.mark.asyncio
async def test_system_net_if_addrs_v4_audit():
    gen = system_net_if_addrs_v4_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing IPv4 net if addrs probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    # Most systems have at least one IPv4 interface (lo or eth/en)
    # but in CI/Docker it might be empty. 
    # Metadata is a dict of interfaces.
    assert isinstance(p2.metadata, dict)
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    assert isinstance(p3, ProgressPayload)
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "interface_count" in res
    assert res["family"] == "IPv4"

@pytest.mark.asyncio
async def test_system_net_if_addrs_v6_audit():
    gen = system_net_if_addrs_v6_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing IPv6 net if addrs probe"
    
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
    assert res["family"] == "IPv6"

@pytest.mark.asyncio
async def test_system_disk_partitions_physical_audit():
    gen = system_disk_partitions_physical_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing physical-partitions probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert isinstance(p2.metadata, dict)
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "physical_partition_count" in res
