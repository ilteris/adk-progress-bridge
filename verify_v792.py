import asyncio
import websockets
import json
import os
import sys

async def verify():
    url = "ws://localhost:8000/ws"
    tools = [
        "system_process_ionice_value_ultimate_audit",
        "system_process_rlimit_nofile_soft_ultimate_audit",
        "system_process_cpu_hard_ultimate_audit", # Wait, I named it system_process_rlimit_cpu_hard_ultimate_audit
        "system_process_rlimit_rss_soft_ultimate_audit",
        "system_process_cpu_times_children_user_avg_ultimate_audit"
    ]
    
    # Correction of tool names in list
    tools = [
        "system_process_ionice_value_ultimate_audit",
        "system_process_rlimit_nofile_soft_ultimate_audit",
        "system_process_rlimit_cpu_hard_ultimate_audit",
        "system_process_rlimit_rss_soft_ultimate_audit",
        "system_process_cpu_times_children_user_avg_ultimate_audit"
    ]

    print(f"Starting v792 verification via WebSocket at {url}...")
    
    try:
        async with websockets.connect(url) as websocket:
            # Consume the "connected" message
            msg = await websocket.recv()
            print(f"Connected message: {msg}")
            
            for tool in tools:
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
                    message = await websocket.recv()
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
                    if count >= 890:
                        print(f"Milestone 890 REACHED (Total: {count}).")
                    else:
                        print(f"Milestone 890 NOT REACHED. Current count: {count}")
                        sys.exit(1)
                    break

    except Exception as e:
        print(f"Verification Error: {e}")
        sys.exit(1)

    print("\nSUPREME APEX VERIFICATION v792: SUCCESS")

if __name__ == "__main__":
    asyncio.run(verify())