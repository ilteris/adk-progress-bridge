import pytest
from backend.app.dummy_tool import system_cpu_times_percent_nice_focused_audit, system_disk_io_read_count_audit, system_disk_io_write_count_audit
from backend.app.bridge import ProgressPayload
import psutil

@pytest.mark.asyncio
async def test_system_cpu_times_percent_nice_focused_audit():
    gen = system_cpu_times_percent_nice_focused_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing nice CPU focused probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "nice_percent" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "final_nice_percent" in res
    assert res["metric"] == "nice_cpu_time"

@pytest.mark.asyncio
async def test_system_disk_io_read_count_audit():
    gen = system_disk_io_read_count_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing disk read count probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "read_count" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "final_read_count" in res

@pytest.mark.asyncio
async def test_system_disk_io_write_count_audit():
    gen = system_disk_io_write_count_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing disk write count probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "write_count" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "final_write_count" in res
