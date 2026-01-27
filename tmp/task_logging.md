# Task: Structured Logging Integration

## Objective
Integrate the structured logger from `backend/app/logger.py` into the backend codebase. Use Python `contextvars` to automatically inject `call_id` and `tool_name` into all logs within a task's execution context.

## Steps
1. **Context Management**: 
   - Create a new file `backend/app/context.py` to manage `call_id` and `tool_name` context variables.
2. **Update Logger**:
   - Modify `backend/app/logger.py`'s `JsonFormatter` to pull `call_id` and `tool_name` from the context variables if they aren't provided in the log record's `extra`.
3. **Integrate into `main.py`**:
   - Set context variables in `start_task` and `stream_task`.
   - Add logging for task initiation, stream start/end, and errors.
   - Add logging to `lifespan` and `cleanup_loop`.
4. **Update `bridge.py`**:
   - Ensure `ToolRegistry` methods use the logger with context.
5. **Update `dummy_tool.py`**:
   - Ensure tools use the logger, which should now automatically pick up the context.

## Verification
- Run the backend.
- Trigger a tool via `curl` or the frontend.
- Check the console output to verify logs are structured JSON and contain `call_id` and `tool_name`.
