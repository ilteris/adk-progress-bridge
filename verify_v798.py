import asyncio
import websockets
import json
import os
import sys

async def verify():
    url = "ws://localhost:8000/ws"
    tools_to_test = [
        "system_process_cpu_times_user_avg_ultimate_audit_v3",
        "system_process_cpu_percent_max_ultimate_audit_v2",
        "system_process_memory_percent_min_ultimate_audit_v3",
        "system_process_num_threads_avg_ultimate_audit_v3",
        "system_process_num_ctx_switches_voluntary_avg_ultimate_audit_v3"
    ]

    print(f"Starting v798 verification via WebSocket at {url}...")
    
    try:
        async with websockets.connect(url) as websocket:
            # Consume the "connected" message
            msg = await websocket.recv()
            print(f"Connected message: {msg}")
            
            for tool in tools_to_test:
                print(f"Verifying {tool}...")
                start_msg = {
                    "type": "start",
                    "tool_name": tool,
                    "args": {"samples": 1},
                    "request_id": f"test-{tool}"
                }
                await websocket.send(json.dumps(start_msg))
                
                result_received = False
                
                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    except asyncio.TimeoutError:
                        print(f"  FAILURE: Timeout waiting for result of {tool}")
                        sys.exit(1)
                        
                    data = json.loads(message)
                    mtype = data.get("type")
                    if mtype == "system_metrics": continue
                    if mtype == "result":
                        if data.get("payload", {}).get("status") == "audit_complete":
                            print(f"  SUCCESS: {tool} verified.")
                            result_received = True
                        else:
                            print(f"  FAILURE: {tool} returned unexpected result: {data}")
                            sys.exit(1)
                        break
                    if mtype == "error":
                        print(f"  FAILURE: {tool} returned error: {data}")
                        sys.exit(1)
                
                if not result_received:
                    print(f"  FAILURE: No result received for {tool}")
                    sys.exit(1)

            list_msg = {"type": "list_tools", "request_id": "final-check"}
            await websocket.send(json.dumps(list_msg))
            while True:
                msg = await websocket.recv()
                data = json.loads(msg)
                if data["type"] == "tools_list":
                    count = len(data["tools"])
                    print(f"Total unique tools: {count}")
                    if count >= 1010:
                        print(f"Milestone 1010 REACHED (Total: {count}).")
                    else:
                        print(f"Milestone 1010 NOT REACHED. Current count: {count}")
                        sys.exit(1)
                    break

    except Exception as e:
        print(f"Verification Error: {e}")
        sys.exit(1)

    print("\nSUPREME APEX VERIFICATION v798: SUCCESS")

if __name__ == "__main__":
    asyncio.run(verify())
