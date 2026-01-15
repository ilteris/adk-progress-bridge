---
description: Verify SSE streaming is working correctly
---

# Verify Stream

## Prerequisites
- Backend server running on port 8000

## Steps

// turbo
1. Run the verification script:
```bash
python verify_stream.py
```

Alternatively, test manually with curl:

2. Start a task:
```bash
curl -X POST http://localhost:8000/start_task/long_audit \
  -H "Content-Type: application/json" \
  -d '{"duration": 3}'
```

3. Note the `call_id` from the response and stream events:
```bash
curl -N http://localhost:8000/stream/{call_id}
```

## Expected Output
- Multiple `progress` events with increasing `pct` values
- Final `result` event with status "complete"
