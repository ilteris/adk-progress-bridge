import pytest
from backend.app.dummy_tool import system_net_io_dropout_audit, system_net_io_errin_audit, system_net_io_errout_audit
from backend.app.bridge import ProgressPayload
import psutil

@pytest.mark.asyncio
async def test_system_net_io_dropout_audit():
    gen = system_net_io_dropout_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert "dropout probe" in p1.step.lower()
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "dropout" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "final_dropout" in res

@pytest.mark.asyncio
async def test_system_net_io_errin_audit():
    gen = system_net_io_errin_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert "errin probe" in p1.step.lower()
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "errin" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "final_errin" in res

@pytest.mark.asyncio
async def test_system_net_io_errout_audit():
    gen = system_net_io_errout_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert "errout probe" in p1.step.lower()
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "errout" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "final_errout" in res
