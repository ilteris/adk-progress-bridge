import pytest
from backend.app.dummy_tool import system_disk_io_read_count_ultimate_audit, system_disk_io_write_count_ultimate_audit, system_disk_io_read_bytes_ultimate_audit
from backend.app.bridge import ProgressPayload

@pytest.mark.anyio
async def test_system_disk_io_read_count_ultimate_audit():
    gen = system_disk_io_read_count_ultimate_audit(samples=1)
    responses = []
    async for resp in gen:
        responses.append(resp)
    
    assert len(responses) >= 3 # Init, Sample, Finalize, Result
    assert any(isinstance(r, ProgressPayload) and r.step == "Finalizing" for r in responses)
    assert responses[-1]["status"] == "audit_complete"
    assert "avg_read_count" in responses[-1]

@pytest.mark.anyio
async def test_system_disk_io_write_count_ultimate_audit():
    gen = system_disk_io_write_count_ultimate_audit(samples=1)
    responses = []
    async for resp in gen:
        responses.append(resp)
    
    assert len(responses) >= 3
    assert any(isinstance(r, ProgressPayload) and r.step == "Finalizing" for r in responses)
    assert responses[-1]["status"] == "audit_complete"
    assert "avg_write_count" in responses[-1]

@pytest.mark.anyio
async def test_system_disk_io_read_bytes_ultimate_audit():
    gen = system_disk_io_read_bytes_ultimate_audit(samples=1)
    responses = []
    async for resp in gen:
        responses.append(resp)
    
    assert len(responses) >= 3
    assert any(isinstance(r, ProgressPayload) and r.step == "Finalizing" for r in responses)
    assert responses[-1]["status"] == "audit_complete"
    assert "avg_read_bytes" in responses[-1]
