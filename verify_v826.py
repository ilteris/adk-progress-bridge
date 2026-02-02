import asyncio
import websockets
import json
import os
import sys

async def verify_v826():
    api_key = os.getenv("BRIDGE_API_KEY", "")
    url = "ws://localhost:8000/ws"
    if api_key:
        url += f"?api_key={api_key}"

    try:
        async with websockets.connect(url) as websocket:
            print("\n--- Verifying v826: SUPREME APEX 2152 TOOLS ---")
            
            # 1. Verify tool count
            list_msg = {
                "type": "list_tools",
                "request_id": "verify-count"
            }
            await websocket.send(json.dumps(list_msg))
            
            while True:
                msg = await websocket.recv()
                data = json.loads(msg)
                if data.get('type') == 'tools_list':
                    count = len(data.get('tools', []))
                    print(f"Tool count: {count}")
                    if count == 2152:
                        print("✅ Tool count verification SUCCESS (2152 tools)")
                    else:
                        print(f"❌ Tool count verification FAILED (expected 2152, got {count})")
                    break

            # 2. Verify execution of a v16 tool
            tool_to_test = "system_cpu_stats_interrupts_avg_v16"
            print(f"\nTesting execution of {tool_to_test}...")
            start_msg = {
                "type": "start",
                "tool_name": tool_to_test,
                "args": {"samples": 5},
                "request_id": "verify-exec"
            }
            await websocket.send(json.dumps(start_msg))
            
            async for message in websocket:
                data = json.loads(message)
                mtype = data.get('type')
                payload = data.get('payload', {})
                
                if mtype == 'progress':
                    print(f"Progress: {payload.get('pct')}% | {payload.get('step')}")
                elif mtype == 'result':
                    print(f"✅ Result: {payload}")
                    if payload.get('status') == 'audit_complete' and 'avg' in payload:
                        print(f"✅ Execution of {tool_to_test} SUCCESS")
                    else:
                        print(f"❌ Execution of {tool_to_test} FAILED (unexpected payload)")
                    break
                elif mtype == 'error':
                    print(f"❌ Error: {payload}")
                    break

    except Exception as e:
        print(f"❌ WS Error in verify_v826: {e}")

if __name__ == "__main__":
    asyncio.run(verify_v826())
