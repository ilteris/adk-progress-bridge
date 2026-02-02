import asyncio
import websockets
import json
import os
import sys

async def run_ws_new_tools_v691():
    api_key = os.getenv("BRIDGE_API_KEY", "")
    url = "ws://localhost:8000/ws"
    if api_key:
        url += f"?api_key={api_key}"

    try:
        async with websockets.connect(url) as websocket:
            print("\n--- Testing new Net IO Average tools (v2.10.17) ---")
            
            new_tools = [
                "system_net_io_errout_avg_audit",
                "system_net_io_dropin_avg_audit",
                "system_net_io_dropout_avg_audit"
            ]
            
            for tool in new_tools:
                start_msg = {
                    "type": "start",
                    "tool_name": tool,
                    "request_id": f"test-{tool}-v691"
                }
                await websocket.send(json.dumps(start_msg))
                print(f"Start message sent for {tool}")
                
                async for message in websocket:
                    data = json.loads(message)
                    mtype = data.get('type')
                    payload = data.get('payload')
                    
                    if mtype == 'progress':
                        print(f"  [{tool}] Progress: {payload.get('pct')}% - {payload.get('step')}")
                    
                    if mtype == 'result':
                         print(f"  [SUCCESS] RESULT for {tool}: {payload}")
                         break
                    if mtype == 'error':
                         print(f"  [ERROR] ERROR for {tool}: {payload}")
                         break
    except Exception as e:
        print(f"WS Error in run_ws_new_tools_v691: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_ws_new_tools_v691())
