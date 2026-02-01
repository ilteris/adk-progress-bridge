import pytest
import asyncio
import time
from unittest.mock import MagicMock
from backend.app.health import HealthEngine

@pytest.mark.asyncio
async def test_health_engine_collection():
    start_time = time.time() - 100
    engine = HealthEngine(start_time)
    
    # Test raw metrics collection
    raw = engine.collect_raw_metrics()
    assert isinstance(raw, dict)
    assert 'sys_mem_total' in raw
    
    # Mock app state with actual values to avoid MagicMock comparison errors
    mock_app_state = MagicMock()
    mock_app_state.last_throughput_time = time.time()
    mock_app_state.last_bytes_received = 0
    mock_app_state.last_bytes_sent = 0
    mock_app_state.last_proc_read_bytes = 0
    mock_app_state.last_proc_write_bytes = 0
    mock_app_state.last_sys_read_bytes = 0
    mock_app_state.last_sys_write_bytes = 0
    mock_app_state.last_sys_net_recv_bytes = 0
    mock_app_state.last_sys_net_sent_bytes = 0
    mock_app_state.last_sys_ctx_switches = 0
    mock_app_state.last_sys_interrupts = 0
    mock_app_state.last_sys_soft_interrupts = 0
    mock_app_state.last_sys_syscalls = 0
    mock_app_state.last_sys_pf_minor = 0
    mock_app_state.last_sys_pf_major = 0
    mock_app_state.peak_ws_connections = 5
    
    # Test health data mapping
    health_data = await engine.get_health_data(
        mock_app_state, 
        app_version="1.7.0", 
        git_commit="v376-test", 
        operational_apex="TEST FIDELITY"
    )
    
    assert health_data["status"] == "healthy"
    assert health_data["version"] == "1.7.0"
    assert health_data["git_commit"] == "v376-test"
    assert health_data["operational_apex"] == "TEST FIDELITY"
    assert "uptime_seconds" in health_data
    assert "system_memory" in health_data
    assert "process_cpu_usage" in health_data
    assert "registry_size" in health_data

@pytest.mark.asyncio
async def test_health_engine_throughput():
    engine = HealthEngine(time.time() - 100)
    mock_app_state = MagicMock()
    mock_app_state.last_throughput_time = time.time() - 2.0  # 2 seconds ago
    mock_app_state.last_bytes_received = 1000
    mock_app_state.last_bytes_sent = 2000
    mock_app_state.last_proc_read_bytes = 0
    mock_app_state.last_proc_write_bytes = 0
    mock_app_state.last_sys_read_bytes = 0
    mock_app_state.last_sys_write_bytes = 0
    mock_app_state.last_sys_net_recv_bytes = 0
    mock_app_state.last_sys_net_sent_bytes = 0
    mock_app_state.last_sys_ctx_switches = 0
    mock_app_state.last_sys_interrupts = 0
    mock_app_state.last_sys_soft_interrupts = 0
    mock_app_state.last_sys_syscalls = 0
    mock_app_state.last_sys_pf_minor = 0
    mock_app_state.last_sys_pf_major = 0
    mock_app_state.peak_ws_connections = 5
    
    # Trigger health data collection
    health_data = await engine.get_health_data(
        mock_app_state, 
        app_version="1.7.0", 
        git_commit="v376-test", 
        operational_apex="TEST FIDELITY"
    )
    
    assert "ws_throughput_bps" in health_data
    assert "disk_io_total" in health_data
    assert "network_io_total" in health_data