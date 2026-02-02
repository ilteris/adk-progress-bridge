import pytest
import asyncio
from backend.app.dummy_tool import (
    system_disk_partitions_count_avg_audit,
    system_disk_io_read_time_avg_audit,
    system_disk_io_write_time_avg_audit
)
from backend.app.bridge import ProgressPayload

@pytest.mark.asyncio
async def test_system_disk_partitions_count_avg_audit():
    gen = system_disk_partitions_count_avg_audit(samples=1)
    results = []
    async for item in gen:
        results.append(item)
    
    assert len(results) >= 2
    assert isinstance(results[0], ProgressPayload)
    assert results[-1]["status"] == "audit_complete"
    assert "avg_disk_partitions_count" in results[-1]

@pytest.mark.asyncio
async def test_system_disk_io_read_time_avg_audit():
    gen = system_disk_io_read_time_avg_audit(samples=1)
    results = []
    async for item in gen:
        results.append(item)
    
    assert len(results) >= 2
    assert isinstance(results[0], ProgressPayload)
    assert results[-1]["status"] == "audit_complete"
    assert "avg_disk_read_time" in results[-1]

@pytest.mark.asyncio
async def test_system_disk_io_write_time_avg_audit():
    gen = system_disk_io_write_time_avg_audit(samples=1)
    results = []
    async for item in gen:
        results.append(item)
    
    assert len(results) >= 2
    assert isinstance(results[0], ProgressPayload)
    assert results[-1]["status"] == "audit_complete"
    assert "avg_disk_write_time" in results[-1]
