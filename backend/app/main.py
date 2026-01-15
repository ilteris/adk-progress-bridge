import asyncio
import uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from .bridge import registry, ProgressEvent, format_sse, ProgressPayload

app = FastAPI(title="ADK Progress Bridge")

# Enable CORS for Vue.js development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/start_task/{tool_name}")
async def start_task(tool_name: str, args: dict = {}):
    tool = registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    call_id = str(uuid.uuid4())
    # Instantiate the generator
    gen = tool(**args)
    registry.store_task(call_id, gen)
    
    return {"call_id": call_id}

@app.get("/stream/{call_id}")
async def stream_task(call_id: str):
    gen = registry.get_task(call_id)
    if not gen:
        raise HTTPException(status_code=404, detail="Task not found or already consumed")

    async def event_generator():
        try:
            async for item in gen:
                if isinstance(item, ProgressPayload):
                    event = ProgressEvent(call_id=call_id, type="progress", payload=item)
                else:
                    # Final result
                    event = ProgressEvent(call_id=call_id, type="result", payload=item)
                yield await format_sse(event)
        except Exception as e:
            event = ProgressEvent(call_id=call_id, type="error", payload={"detail": str(e)})
            yield await format_sse(event)
        finally:
            registry.remove_task(call_id)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Import tools to register them
from . import dummy_tool
