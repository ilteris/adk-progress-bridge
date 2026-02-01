import pytest
import asyncio
from backend.app.dummy_tool import system_virtual_memory_audit, system_swap_memory_audit, system_disk_usage_audit
from backend.app.bridge import ProgressPayload

@pytest.mark.asyncio
async def test_system_virtual_memory_audit():
    gen = system_virtual_memory_audit(samples=1)
    async for item in gen:
        if isinstance(item, ProgressPayload):
            assert item.step in ["Initializing memory probe", "Sampling virtual memory", "Finalizing"]
            if item.step == "Sampling virtual memory":
                assert "percent" in item.metadata
                assert "available" in item.metadata
        else:
            assert item["status"] == "audit_complete"
            assert "final_vmem" in item

@pytest.mark.asyncio
async def test_system_swap_memory_audit():
    gen = system_swap_memory_audit(samples=1)
    async for item in gen:
        if isinstance(item, ProgressPayload):
            assert item.step in ["Initializing swap probe", "Sampling swap memory", "Finalizing"]
            if item.step == "Sampling swap memory":
                assert "percent" in item.metadata
                assert "used" in item.metadata
        else:
            assert item["status"] == "audit_complete"
            assert "final_swap" in item

@pytest.mark.asyncio
async def test_system_disk_usage_audit():
    gen = system_disk_usage_audit(samples=1, path="/")
    async for item in gen:
        if isinstance(item, ProgressPayload):
            assert item.step in ["Initializing disk probe", "Sampling disk usage", "Finalizing"]
            if item.step == "Sampling disk usage":
                if "error" not in item.metadata:
                    assert "percent" in item.metadata
                    assert "free" in item.metadata
        else:
            assert item["status"] == "audit_complete"
            assert "final_usage" in item
