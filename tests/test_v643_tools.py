import pytest
from backend.app.dummy_tool import system_cpu_times_percent_irq_focused_audit, system_cpu_times_percent_softirq_focused_audit, system_net_io_errors_audit
from backend.app.bridge import ProgressPayload
import psutil

@pytest.mark.asyncio
async def test_system_cpu_times_percent_irq_focused_audit():
    gen = system_cpu_times_percent_irq_focused_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing IRQ CPU focused probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "irq_percent" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "final_irq_percent" in res
    assert res["metric"] == "irq_cpu_time"

@pytest.mark.asyncio
async def test_system_cpu_times_percent_softirq_focused_audit():
    gen = system_cpu_times_percent_softirq_focused_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing soft IRQ CPU focused probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "softirq_percent" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "final_softirq_percent" in res
    assert res["metric"] == "softirq_cpu_time"

@pytest.mark.asyncio
async def test_system_net_io_errors_audit():
    gen = system_net_io_errors_audit(samples=1)
    
    # First yield is ProgressPayload
    p1 = await gen.__anext__()
    assert isinstance(p1, ProgressPayload)
    assert p1.step == "Initializing network error probe"
    
    # Second yield is ProgressPayload (sample)
    p2 = await gen.__anext__()
    assert isinstance(p2, ProgressPayload)
    assert "errin" in p2.metadata
    
    # Third yield is ProgressPayload (finalizing)
    p3 = await gen.__anext__()
    
    # Fourth yield is the result dict
    res = await gen.__anext__()
    assert res["status"] == "audit_complete"
    assert "final_errors" in res
