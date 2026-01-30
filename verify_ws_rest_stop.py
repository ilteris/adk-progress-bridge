import asyncio
import websockets
import json
import requests
import time
import threading
import os

async def test_ws_stop_via_rest():
    api_key = os.getenv("BRIDGE_API_KEY", "")
    url = f"ws://localhost:8000/ws"
    if api_key:
        url += f"?api_key={api_key}"
    base_url = "http://localhost:8000"
    
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key
    
    async with websockets.connect(url) as websocket:
        print("\n--- Testing WS Start + REST Stop ---")
        
        start_msg = {
            "type": "start",
            "tool_name": "long_audit",
            "args": {"duration": 10},
            "request_id": "ws-start"
        }
        await websocket.send(json.dumps(start_msg))
        
        call_id = None
        
        async for message in websocket:
            data = json.loads(message)
            if data['type'] == 'task_started':
                call_id = data['call_id']
                print(f"Task started via WS. Call ID: {call_id}")
                
                # Stop via REST after 1 second
                def stop_via_rest():
                    time.sleep(1)
                    print(f"Sending REST stop request for {call_id}...")
                    resp = requests.post(f"{base_url}/stop_task/{call_id}", headers=headers)
                    print(f"REST stop response: {resp.status_code} | {resp.json()}")
                
                threading.Thread(target=stop_via_rest).start()
            
            if data['type'] == 'progress':
                payload = data['payload']
                print(f"WS Progress: {payload.get('step')} ({payload.get('pct')}%) ")
                if payload.get('step') == 'Cancelled':
                    print("SUCCESS: Task cancelled signal received via WS")
                    break
            
            if data['type'] == 'result':
                print("Task finished normally (Stop failed?)")
                break
            
            if data['type'] == 'error':
                print(f"WS Error: {data['payload']}")
                break

if __name__ == "__main__":
    asyncio.run(test_ws_stop_via_rest())