import pytest
from backend.app.dummy_tool import system_net_io_packets_sent_avg_audit, system_net_io_packets_recv_avg_audit, system_net_io_errin_avg_audit
from backend.app.bridge import ProgressPayload

@pytest.mark.asyncio
async def test_system_net_io_packets_sent_avg_audit():
    gen = system_net_io_packets_sent_avg_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing Net IO probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "net_packets_sent" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    assert isinstance(p3, ProgressPayload)
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "avg_net_packets_sent" in res

@pytest.mark.asyncio
async def test_system_net_io_packets_recv_avg_audit():
    gen = system_net_io_packets_recv_avg_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing Net IO probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "net_packets_recv" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "avg_net_packets_recv" in res

@pytest.mark.asyncio
async def test_system_net_io_errin_avg_audit():
    gen = system_net_io_errin_avg_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing Net IO probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "net_errors_in" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "avg_net_errors_in" in res
