import pytest
from backend.app.dummy_tool import system_disk_usage_percent_avg_audit, system_disk_usage_used_avg_audit, system_disk_usage_free_avg_audit
from backend.app.bridge import ProgressPayload

@pytest.mark.asyncio
async def test_system_disk_usage_percent_avg_audit():
    gen = system_disk_usage_percent_avg_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing Disk probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "disk_percent" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    assert isinstance(p3, ProgressPayload)
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "avg_disk_percent" in res

@pytest.mark.asyncio
async def test_system_disk_usage_used_avg_audit():
    gen = system_disk_usage_used_avg_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing Disk probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "disk_used" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "avg_disk_used" in res

@pytest.mark.asyncio
async def test_system_disk_usage_free_avg_audit():
    gen = system_disk_usage_free_avg_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing Disk probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "disk_free" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "avg_disk_free" in res
