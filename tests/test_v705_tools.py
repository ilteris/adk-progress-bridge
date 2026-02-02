import pytest
from backend.app.dummy_tool import system_swap_memory_sin_ultimate_audit, system_swap_memory_sout_ultimate_audit, system_disk_io_busy_time_ultimate_audit
from backend.app.bridge import ProgressPayload

@pytest.mark.anyio
async def test_system_swap_memory_sin_ultimate_audit():
    gen = system_swap_memory_sin_ultimate_audit(samples=1)
    responses = []
    async for resp in gen:
        responses.append(resp)
    
    assert len(responses) >= 3 # Init, Sample, Finalize, Result
    assert any(isinstance(r, ProgressPayload) and r.step == "Finalizing" for r in responses)
    assert responses[-1]["status"] == "audit_complete"
    assert "avg_swap_sin" in responses[-1]

@pytest.mark.anyio
async def test_system_swap_memory_sout_ultimate_audit():
    gen = system_swap_memory_sout_ultimate_audit(samples=1)
    responses = []
    async for resp in gen:
        responses.append(resp)
    
    assert len(responses) >= 3
    assert any(isinstance(r, ProgressPayload) and r.step == "Finalizing" for r in responses)
    assert responses[-1]["status"] == "audit_complete"
    assert "avg_swap_sout" in responses[-1]

@pytest.mark.anyio
async def test_system_disk_io_busy_time_ultimate_audit():
    gen = system_disk_io_busy_time_ultimate_audit(samples=1)
    responses = []
    async for resp in gen:
        responses.append(resp)
    
    assert len(responses) >= 3
    assert any(isinstance(r, ProgressPayload) and r.step == "Finalizing" for r in responses)
    assert responses[-1]["status"] == "audit_complete"
    assert "avg_busy_time" in responses[-1]