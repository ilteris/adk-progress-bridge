---
description: Verify SSE streaming is working correctly
---

# Verify Stream

## Prerequisites
- Backend server running on port 8000

## Steps

1. Run the verification script:
```bash
# If BRIDGE_API_KEY is set, the script must handle it (not yet updated)
python verify_stream.py
```

Alternatively, test manually with curl (authenticated):

2. Start a task:
```bash
curl -X POST http://localhost:8000/start_task/long_audit \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${BRIDGE_API_KEY}" \
  -d '{"duration": 3}'
```

3. Note the `call_id` from the response and stream events:
```bash
# API Key can be passed as a query parameter for SSE
curl -N "http://localhost:8000/stream/{call_id}?api_key=${BRIDGE_API_KEY}"
```

## Expected Output
- Multiple `progress` events with increasing `pct` values
- Final `result` event with status "complete"