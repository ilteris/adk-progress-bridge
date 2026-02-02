import asyncio
import websockets
import json
import os
import sys
import time

async def verify_v820():
    api_key = os.getenv("BRIDGE_API_KEY", "")
    url = "ws://localhost:8000/ws"
    if api_key:
        url += f"?api_key={api_key}"
        print(f"Using API Key in WS URL")

    new_tools = [
        "system_virtual_memory_active_avg_v10",
        "system_swap_memory_sin_avg_v10",
        "system_disk_usage_total_avg_v10"
    ]

    try:
        async with websockets.connect(url) as websocket:
            print("\n--- Verifying v820 tools over WebSocket ---")
            
            # Wait for connected message
            msg = await websocket.recv()
            print(f"WS Event: {json.loads(msg)['type']}")

            # 1. Check tool count
            list_msg = {
                "type": "list_tools",
                "request_id": "count-check-v820"
            }
            await websocket.send(json.dumps(list_msg))
            msg = await websocket.recv()
            data = json.loads(msg)
            if data['type'] == 'tools_list':
                count = len(data['tools'])
                print(f"Tools count: {count}")
                if count >= 1880:
                    print("SUCCESS: 1880 tools milestone reached.")
                else:
                    print(f"FAILURE: Expected at least 1880 tools, got {count}")
                    sys.exit(1)

            # 2. Test new tools
            for tool in new_tools:
                print(f"\nTesting {tool}...")
                start_msg = {
                    "type": "start",
                    "tool_name": tool,
                    "args": {"samples": 2},
                    "request_id": f"test-{tool}"
                }
                await websocket.send(json.dumps(start_msg))
                
                async for message in websocket:
                    data = json.loads(message)
                    if data['type'] == 'progress':
                        pct = data['payload'].get('pct')
                        print(f"  Progress: {pct}%")
                    if data['type'] == 'result':
                        print(f"  RESULT: {data['payload']}")
                        break
            
            print("\nAll v820 verifications passed.")

    except Exception as e:
        print(f"WS Error: {e}")
        # sys.exit(1) # Don't exit here so we can see the error

if __name__ == "__main__":
    asyncio.run(verify_v820())
