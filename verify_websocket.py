import asyncio
import websockets
import json
import os
import sys
import time

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
                "args": {"duration": 10},
                "request_id": "test-start-1"
            }
            await websocket.send(json.dumps(start_msg))
            print("Start message sent for long_audit")
            
            call_id = None
            async for message in websocket:
                data = json.loads(message)
                mtype = data['type']
                payload = data.get('payload', {})
                
                print(f"WS Event: {mtype} | {payload.get('step') if isinstance(payload, dict) else payload}")
                
                if not call_id and data.get('call_id'):
                    call_id = data['call_id']
                
                # After a few steps, try to stop it
                if mtype == 'progress' and isinstance(payload, dict) and payload.get('pct', 0) >= 20:
                    print(f"Reaching 20%, sending STOP for {call_id}")
                    stop_msg = {
                        "type": "stop",
                        "call_id": call_id,
                        "request_id": "test-stop-1"
                    }
                    await websocket.send(json.dumps(stop_msg))
                
                if mtype == 'stop_success' and data.get('request_id') == 'test-stop-1':
                    print("Received stop_success acknowledgement")
                
                if mtype == 'progress' and isinstance(payload, dict) and payload.get('step') == 'Cancelled':
                    print("Received Cancelled confirmation from server")
                    break
                
                if mtype == 'result' or mtype == 'error':
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
                "args": {},
                "request_id": "test-interactive-1"
            }
            await websocket.send(json.dumps(start_msg))
            print("Start message sent for interactive_task")
            
            call_id = None
            async for message in websocket:
                data = json.loads(message)
                mtype = data['type']
                payload = data.get('payload', {})
                
                print(f"WS Event: {mtype} | {payload.get('step') if isinstance(payload, dict) else payload}")
                
                if not call_id and data.get('call_id'):
                    call_id = data['call_id']

                if mtype == 'input_request':
                    prompt = payload.get('prompt')
                    print(f"RECEIVED INPUT REQUEST: {prompt}")
                    # Send response
                    input_msg = {
                        "type": "input",
                        "call_id": call_id,
                        "value": "yes",
                        "request_id": "test-input-1"
                    }
                    await websocket.send(json.dumps(input_msg))
                    print("Sent input response: yes")
                
                if mtype == 'input_success' and data.get('request_id') == 'test-input-1':
                    print("Received input_success acknowledgement")

                if mtype == 'result':
                    print(f"FINAL RESULT: {payload}")
                    break
                
                if mtype == 'error':
                    print(f"ERROR: {payload}")
                    break
                    
    except Exception as e:
        print(f"WS Error in test_ws_interactive: {e}")

async def run_ws_robustness():
    api_key = os.getenv("BRIDGE_API_KEY", "")
    url = "ws://localhost:8000/ws"
    if api_key:
        url += f"?api_key={api_key}"

    try:
        async with websockets.connect(url) as websocket:
            print("\n--- Testing Robustness & Error Handling ---")
            
            # 1. Test ping/pong
            print("Sending ping...")
            await websocket.send(json.dumps({"type": "ping"}))
            msg = await websocket.recv()
            data = json.loads(msg)
            print(f"Received: {data['type']}")
            
            # 2. Test Invalid JSON
            print("Sending invalid JSON...")
            await websocket.send("not-json")
            msg = await websocket.recv()
            data = json.loads(msg)
            print(f"Received error: {data['payload']['detail']}")
            
            # 3. Test Unknown Message Type
            print("Sending unknown message type...")
            await websocket.send(json.dumps({"type": "unknown_cmd", "request_id": "req-unknown"}))
            msg = await websocket.recv()
            data = json.loads(msg)
            print(f"Received error: {data['payload']['detail']}")
            
            # 4. Test Message Size Limit
            print("Sending message too large...")
            large_data = "x" * (1024 * 1024 + 100) # > 1MB
            await websocket.send(large_data)
            msg = await websocket.recv()
            data = json.loads(msg)
            print(f"Received error: {data['payload']['detail']}")
            
            print("Robustness verification SUCCESS")
            
    except Exception as e:
        print(f"WS Error in run_ws_robustness: {e}")

async def run_ws_list_tools():
    api_key = os.getenv("BRIDGE_API_KEY", "")
    url = "ws://localhost:8000/ws"
    if api_key:
        url += f"?api_key={api_key}"

    try:
        async with websockets.connect(url) as websocket:
            print("\n--- Testing list_tools flow ---")
            list_msg = {
                "type": "list_tools",
                "request_id": "list-tools-test"
            }
            await websocket.send(json.dumps(list_msg))
            
            message = await websocket.recv()
            data = json.loads(message)
            print(f"WS Event: {data['type']} | Tools: {data.get('tools')}")
            if data['type'] == 'tools_list' and 'long_audit' in data['tools']:
                print("list_tools verification SUCCESS")
            else:
                print("list_tools verification FAILED")
    except Exception as e:
        print(f"WS Error in run_ws_list_tools: {e}")

async def run_ws_stress_concurrency():
    api_key = os.getenv("BRIDGE_API_KEY", "")
    url = "ws://localhost:8000/ws"
    if api_key:
        url += f"?api_key={api_key}"

    print("\n--- Testing Concurrency Stress (v162) ---")
    try:
        async with websockets.connect(url) as websocket:
            num_tasks = 10
            print(f"Starting {num_tasks} tasks simultaneously over ONE WebSocket connection...")
            
            for i in range(num_tasks):
                start_msg = {
                    "type": "start",
                    "tool_name": "long_audit",
                    "args": {"duration": 2},
                    "request_id": f"stress-{i}"
                }
                await websocket.send(json.dumps(start_msg))
            
            results_received = 0
            tasks_started = 0
            
            async for message in websocket:
                data = json.loads(message)
                mtype = data['type']
                
                if mtype == 'task_started':
                    tasks_started += 1
                elif mtype == 'result':
                    results_received += 1
                elif mtype == 'error':
                    print(f"Error during stress test: {data['payload']}")
                
                if results_received == num_tasks:
                    print(f"All {num_tasks} concurrent tasks completed successfully!")
                    break
            
            if tasks_started == num_tasks and results_received == num_tasks:
                print("Concurrency stress verification SUCCESS")
            else:
                print(f"Concurrency stress verification FAILED: started={tasks_started}, finished={results_received}")
                
    except Exception as e:
        print(f"WS Error in run_ws_stress_concurrency: {e}")

async def main():
    await run_ws_full()
    await run_ws_interactive()
    await run_ws_list_tools()
    await run_ws_robustness()
    await run_ws_stress_concurrency()

if __name__ == "__main__":
    asyncio.run(main())
