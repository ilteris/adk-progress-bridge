import pytest
from backend.app.dummy_tool import system_net_if_addrs_ptp_audit, system_disk_partitions_opts_audit, system_cpu_times_percent_iowait_focused_audit
from backend.app.bridge import ProgressPayload
import psutil

@pytest.mark.asyncio
async def test_system_net_if_addrs_ptp_audit():
    gen = system_net_if_addrs_ptp_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing PTP net if addrs probe"
    
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
    assert res["family"] == "PTP"

@pytest.mark.asyncio
async def test_system_disk_partitions_opts_audit():
    # Use 'rw' as default opts to check
    opts = "rw"
    
    gen = system_disk_partitions_opts_audit(samples=1, opts=opts)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing opts-partitions probe"
    
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
    assert res["opts"] == opts

@pytest.mark.asyncio
async def test_system_cpu_times_percent_iowait_focused_audit():
    gen = system_cpu_times_percent_iowait_focused_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing I/O wait CPU focused probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "iowait_percent" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "final_iowait_percent" in res
    assert res["metric"] == "iowait_cpu_time"
