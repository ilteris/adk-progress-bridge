import pytest
import asyncio
import httpx
import re
from backend.app.main import app
from httpx import ASGITransport

def get_metric_value(metrics_text: str, metric_name: str, labels: dict = None) -> float:
    """
    Parses a prometheus metric value from the text output.
    Example: adk_task_progress_steps_total{tool_name="security_scan"} 2.0
    """
    label_str = ""
    if labels:
        label_parts = [f'{k}="{v}"' for k, v in labels.items()]
        label_str = r'\{' + ",".join(label_parts) + r'\}'
    else:
        # Match metric without labels or with any labels if none specified
        label_str = r'(\{.*?\})?'
    
    pattern = rf'^{metric_name}{label_str}\s+([\d.e+-]+)'
    match = re.search(pattern, metrics_text, re.MULTILINE)
    if match:
        return float(match.group(match.lastindex))
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
        initial_progress = get_metric_value(
            initial_metrics_res.text, 
            "adk_task_progress_steps_total", 
            {"tool_name": "security_scan"}
        )
        initial_total = get_metric_value(
            initial_metrics_res.text,
            "adk_tasks_total",
            {"status": "success", "tool_name": "security_scan"}
        )

        # 1. Start a task
        start_res = await client.post("/start_task/security_scan", json={"target": "test"})
        assert start_res.status_code == 200
        call_id = start_res.json()["call_id"]
        
        # 2. Check active tasks metric
        metrics_res = await client.get("/metrics")
        # For gauge, we check absolute value as we just started it
        assert f'adk_active_tasks{{tool_name="security_scan"}} 1.0' in metrics_res.text
        
        # 3. Stream the task
        async with client.stream("GET", f"/stream/{call_id}") as response:
            async for line in response.aiter_lines():
                pass
        
        # 4. Check completion metrics
        metrics_res = await client.get("/metrics")
        print(f"DEBUG METRICS:\n{metrics_res.text}")
        
        assert f'adk_active_tasks{{tool_name="security_scan"}} 0.0' in metrics_res.text
        
        current_total = get_metric_value(
            metrics_res.text,
            "adk_tasks_total",
            {"status": "success", "tool_name": "security_scan"}
        )
        assert current_total == initial_total + 1.0

        current_progress = get_metric_value(
            metrics_res.text,
            "adk_task_progress_steps_total",
            {"tool_name": "security_scan"}
        )
        # security_scan yields 2 progress payloads
        assert current_progress == initial_progress + 2.0
