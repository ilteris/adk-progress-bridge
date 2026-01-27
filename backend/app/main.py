import asyncio
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from .bridge import registry, ProgressEvent, format_sse, ProgressPayload

async def cleanup_loop(max_age: int = 300, interval: int = 60):
    """Background loop to clean up stale tasks."""
    while True:
        try:
            await asyncio.sleep(interval)
            await registry.cleanup_stale_tasks(max_age)
        except asyncio.CancelledError:
            break
        except Exception:
            pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start cleanup loop
    cleanup_task = asyncio.create_task(cleanup_loop())
    yield
    # Stop cleanup loop
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    # Shutdown logic: Close all active generators
    await registry.cleanup_tasks()

app = FastAPI(
    title="ADK Progress Bridge",
    lifespan=lifespan
)

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
    
    try:
        # Instantiate the generator (will trigger validation via pydantic.validate_call)
        gen = tool(**args)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
    except TypeError as e:
        # Fallback for other argument-related errors
        raise HTTPException(status_code=400, detail=str(e))
    
    call_id = str(uuid.uuid4())
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