import asyncio
import websockets
import json
import os
import sys

async def test_ws_full():
    api_key = os.getenv("BRIDGE_API_KEY", "")
    url = "ws://localhost:8000/ws"
    if api_key:
        url += f"?api_key={api_key}"
        print(f"Using API Key in WS URL")

    try:
        async with websockets.connect(url) as websocket:
            print("Connected to WebSocket")
            
            # 1. Test Start Task
            start_msg = {
                "type": "start",
                "tool_name": "long_audit",
                "args": {"duration": 10}
            }
            await websocket.send(json.dumps(start_msg))
            print("Start message sent for long_audit")
            
            call_id = None
            async for message in websocket:
                data = json.loads(message)
                print(f"WS Event: {data['type']} | {data.get('payload', {}).get('step') or data.get('payload')}")
                
                if not call_id and data.get('call_id'):
                    call_id = data['call_id']
                    print(f"Captured Call ID: {call_id}")
                
                # After a few steps, try to stop it
                if data['type'] == 'progress' and data['payload'].get('pct', 0) >= 20:
                    print(f"Reaching 20%, sending STOP for {call_id}")
                    stop_msg = {
                        "type": "stop",
                        "call_id": call_id
                    }
                    await websocket.send(json.dumps(stop_msg))
                
                if data['type'] == 'progress' and data['payload'].get('step') == 'Cancelled':
                    print("Received Cancelled confirmation from server")
                    break
                
                if data['type'] == 'result' or data['type'] == 'error':
                    break
            
            print("Test finished.")
                    
    except Exception as e:
        print(f"WS Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws_full())
