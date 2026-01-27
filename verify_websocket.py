import asyncio
import websockets
import json
import os
import sys

async def run_ws_full():
    api_key = os.getenv("BRIDGE_API_KEY", "")
    url = "ws://localhost:8000/ws"
    if api_key:
        url += f"?api_key={api_key}"
        print(f"Using API Key in WS URL")

    try:
        async with websockets.connect(url) as websocket:
            print("\n--- Testing start/stop flow ---")
            
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
                    
    except Exception as e:
        print(f"WS Error in test_ws_full: {e}")

async def run_ws_interactive():
    api_key = os.getenv("BRIDGE_API_KEY", "")
    url = "ws://localhost:8000/ws"
    if api_key:
        url += f"?api_key={api_key}"

    try:
        async with websockets.connect(url) as websocket:
            print("\n--- Testing interactive flow ---")
            
            # 1. Start interactive task
            start_msg = {
                "type": "start",
                "tool_name": "interactive_task",
                "args": {}
            }
            await websocket.send(json.dumps(start_msg))
            print("Start message sent for interactive_task")
            
            call_id = None
            async for message in websocket:
                data = json.loads(message)
                mtype = data['type']
                payload = data.get('payload', {})
                
                print(f"WS Event: {mtype} | {payload.get('step') or payload}")
                
                if not call_id and data.get('call_id'):
                    call_id = data['call_id']

                if mtype == 'input_request':
                    prompt = payload.get('prompt')
                    print(f"RECEIVED INPUT REQUEST: {prompt}")
                    # Send response
                    input_msg = {
                        "type": "input",
                        "call_id": call_id,
                        "value": "yes"
                    }
                    await websocket.send(json.dumps(input_msg))
                    print("Sent input response: yes")
                
                if mtype == 'result':
                    print(f"FINAL RESULT: {payload}")
                    break
                
                if mtype == 'error':
                    print(f"ERROR: {payload}")
                    break
                    
    except Exception as e:
        print(f"WS Error in test_ws_interactive: {e}")

async def main():
    # We need the server running. Assuming it's already running or we start it.
    # For this script, we assume it's running on localhost:8000
    await run_ws_full()
    await run_ws_interactive()

if __name__ == "__main__":
    asyncio.run(main())