import pytest
from backend.app.dummy_tool import system_cpu_times_percent_per_cpu_audit, system_net_if_stats_extended_audit, system_disk_partitions_usage_audit
from backend.app.bridge import ProgressPayload

@pytest.mark.asyncio
async def test_system_cpu_times_percent_per_cpu_audit():
    gen = system_cpu_times_percent_per_cpu_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing per-CPU percent probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "cpu_0" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    assert isinstance(p3, ProgressPayload)
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "cpu_count" in res

@pytest.mark.asyncio
async def test_system_net_if_stats_extended_audit():
    gen = system_net_if_stats_extended_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert len(p2.metadata) > 0
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "interface_count" in res

@pytest.mark.asyncio
async def test_system_disk_partitions_usage_audit():
    gen = system_disk_partitions_usage_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    # metadata should contain at least one partition usage if available
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "partition_count" in res
