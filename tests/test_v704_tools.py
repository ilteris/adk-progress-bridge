import pytest
from backend.app.dummy_tool import system_swap_memory_percent_avg_audit, system_swap_memory_used_avg_audit, system_swap_memory_free_avg_audit
from backend.app.bridge import ProgressPayload

@pytest.mark.anyio
async def test_system_swap_memory_percent_avg_audit():
    gen = system_swap_memory_percent_avg_audit(samples=1)
    responses = []
    async for resp in gen:
        responses.append(resp)
    
    assert len(responses) >= 3 # Init, Sample, Finalize, Result
    assert any(isinstance(r, ProgressPayload) and r.step == "Finalizing" for r in responses)
    assert responses[-1]["status"] == "audit_complete"
    assert "avg_swap_percent" in responses[-1]

@pytest.mark.anyio
async def test_system_swap_memory_used_avg_audit():
    gen = system_swap_memory_used_avg_audit(samples=1)
    responses = []
    async for resp in gen:
        responses.append(resp)
    
    assert len(responses) >= 3
    assert any(isinstance(r, ProgressPayload) and r.step == "Finalizing" for r in responses)
    assert responses[-1]["status"] == "audit_complete"
    assert "avg_swap_used" in responses[-1]

@pytest.mark.anyio
async def test_system_swap_memory_free_avg_audit():
    gen = system_swap_memory_free_avg_audit(samples=1)
    responses = []
    async for resp in gen:
        responses.append(resp)
    
    assert len(responses) >= 3
    assert any(isinstance(r, ProgressPayload) and r.step == "Finalizing" for r in responses)
    assert responses[-1]["status"] == "audit_complete"
    assert "avg_swap_free" in responses[-1]
