import asyncio
import websockets
import json
import os
import sys

async def test_ws():
    api_key = os.getenv("BRIDGE_API_KEY", "")
    url = "ws://localhost:8000/ws"
    if api_key:
        url += f"?api_key={api_key}"
        print(f"Using API Key in WS URL")

    try:
        async with websockets.connect(url) as websocket:
            print("Connected to WebSocket")
            
            # Start task
            start_msg = {
                "type": "start",
                "tool_name": "long_audit",
                "args": {"duration": 2}
            }
            await websocket.send(json.dumps(start_msg))
            print("Start message sent")
            
            async for message in websocket:
                data = json.loads(message)
                print(f"WS Event: {data['type']} | {data['payload']}")
                if data['type'] == 'result' or data['type'] == 'error':
                    break
                    
    except Exception as e:
        print(f"WS Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
