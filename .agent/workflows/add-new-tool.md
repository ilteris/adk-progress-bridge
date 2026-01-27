---
description: How to add a new progress-streaming tool to the backend
---

# Add a New Tool

## Steps

1. Create a new file in `backend/app/` (e.g., `my_tool.py`):
```python
import asyncio
from .bridge import progress_tool, ProgressPayload

@progress_tool(name="my_tool_name")
async def my_tool(arg1: str, arg2: int = 10):
    """
    Description of what this tool does.
    """
    total_steps = 5
    
    for i in range(total_steps):
        # Yield progress updates
        yield ProgressPayload(
            step=f"Step {i+1} of {total_steps}",
            pct=int(((i + 1) / total_steps) * 100),
            log=f"Processing: {arg1}"
        )
        await asyncio.sleep(1)  # Simulate work
    
    # Yield final result (must be a dict)
    yield {
        "status": "complete",
        "summary": f"Processed {arg1} successfully"
    }
```

2. Register the tool by importing it in `backend/app/main.py`:
```python
# At the bottom of main.py
from . import my_tool
```

3. Test the tool (requires `X-API-Key` header if `BRIDGE_API_KEY` is set):
```bash
curl -X POST http://localhost:8000/start_task/my_tool_name \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${BRIDGE_API_KEY}" \
  -d '{"arg1": "test"}'
```

## Important Rules
- Tool MUST be an async generator function
- Tool MUST use `@progress_tool` decorator
- Progress updates MUST use `ProgressPayload`
- Final result MUST be a `dict`