import pytest
import asyncio
import httpx
import re
from backend.app.main import app
from httpx import ASGITransport

def get_metric_value(metrics_text, metric_name, labels=None):
    """
    Helper to extract a metric value from the prometheus text format.
    """
    pattern = re.escape(metric_name)
    if labels:
        label_str = ",".join([f'{k}="{v}"' for k, v in labels.items()])
        pattern += re.escape("{") + ".*" + re.escape(label_str) + ".*" + re.escape("}")
    pattern += r"\s+(\d+\.\d+)"
    
    match = re.search(pattern, metrics_text)
    if match:
        return float(match.group(1))
    return 0.0

@pytest.mark.asyncio
async def test_metrics_endpoint():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert "adk_task_duration_seconds" in response.text
        assert "adk_tasks_total" in response.text
        assert "adk_active_tasks" in response.text
        assert "adk_stale_tasks_cleaned_total" in response.text
        assert "adk_task_progress_steps_total" in response.text

@pytest.mark.asyncio
async def test_task_metrics_increment():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 0. Get initial metrics
        initial_metrics_res = await client.get("/metrics")
        initial_total = get_metric_value(initial_metrics_res.text, "adk_tasks_total", {"status": "success", "tool_name": "security_scan"})
        initial_steps = get_metric_value(initial_metrics_res.text, "adk_task_progress_steps_total", {"tool_name": "security_scan"})

        # 1. Start a task
        start_res = await client.post("/start_task/security_scan", json={"target": "test"})
        assert start_res.status_code == 200
        call_id = start_res.json()["call_id"]
        
        # 2. Check active tasks metric
        metrics_res = await client.get("/metrics")
        # active_tasks is a gauge, it might be > 1 if other tests left it running, 
        # but for this specific tool and call_id we expect it to be at least 1.0
        assert f'adk_active_tasks{{tool_name="security_scan"}}' in metrics_res.text
        
        # 3. Stream the task
        async with client.stream("GET", f"/stream/{call_id}") as response:
            async for line in response.aiter_lines():
                pass
        
        # 4. Check completion metrics
        metrics_res = await client.get("/metrics")
        print(f"DEBUG METRICS:\n{metrics_res.text}")
        
        final_total = get_metric_value(metrics_res.text, "adk_tasks_total", {"status": "success", "tool_name": "security_scan"})
        final_steps = get_metric_value(metrics_res.text, "adk_task_progress_steps_total", {"tool_name": "security_scan"})

        assert final_total == initial_total + 1.0
        # security_scan yields 2 progress payloads
        assert final_steps == initial_steps + 2.0
