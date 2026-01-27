# Plan: Backend Input Validation

## Objective
Enhance validation for `args` passed to `start_task` in `backend/app/main.py`. Ensure `args` match the expected parameters of the tool being called.

## Proposed Changes

### 1. Backend Bridge (`backend/app/bridge.py`)
- Implement a helper function `validate_tool_args(tool_func, args)` that uses `inspect.signature` to:
    - Identify required arguments.
    - Identify optional arguments.
    - Check for unexpected arguments (unless `**kwargs` is present).
    - Return a list of error messages or `None` if valid.

### 2. Backend Main (`backend/app/main.py`)
- Update `start_task` endpoint to:
    - Call `validate_tool_args`.
    - Raise `HTTPException(status_code=400)` with detailed error messages if validation fails.

## Verification
- Create a test script or use `curl` to test:
    - Valid arguments.
    - Missing required arguments.
    - Unexpected arguments.
    - Incorrect type of `args` (e.g., not a dict).
