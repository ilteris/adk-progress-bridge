import asyncio
import websockets
import json
import os
import sys

async def verify():
    url = "ws://localhost:8000/ws"
    tools = [
        "system_memory_full_info_text_avg_ultimate_audit",
        "system_memory_full_info_text_max_ultimate_audit",
        "system_memory_full_info_text_min_ultimate_audit",
        "system_memory_full_info_lib_avg_ultimate_audit",
        "system_memory_full_info_lib_max_ultimate_audit",
        "system_memory_full_info_lib_min_ultimate_audit",
        "system_net_io_per_nic_bytes_sent_total_ultimate_audit",
        "system_net_io_per_nic_bytes_recv_total_ultimate_audit",
        "system_memory_full_info_swap_avg_ultimate_audit",
        "system_memory_full_info_swap_max_ultimate_audit"
    ]
    
    print(f"Starting v780 verification via WebSocket at {url}...")
    
    try:
        async with websockets.connect(url) as websocket:
            # Wait for connected message
            msg = await websocket.recv()
            print(f"Connected: {msg}")
            
            for tool in tools:
                print(f"Verifying {tool}...")
                start_msg = {
                    "type": "start",
                    "tool_name": tool,
                    "args": {"samples": 2},
                    "request_id": f"test-{tool}"
                }
                await websocket.send(json.dumps(start_msg))
                
                result_received = False
                progress_count = 0
                
                async for message in websocket:
                    data = json.loads(message)
                    mtype = data.get("type")
                    
                    if mtype == "progress":
                        progress_count += 1
                    
                    if mtype == "result":
                        if data.get("payload", {}).get("status") == "audit_complete":
                            print(f"  SUCCESS: {tool} verified. Progress events: {progress_count}")
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

            # Final check for total tool count
            list_msg = {"type": "list_tools", "request_id": "final-check"}
            await websocket.send(json.dumps(list_msg))
            msg = await websocket.recv()
            data = json.loads(msg)
            if data["type"] == "tools_list":
                count = len(data["tools"])
                print(f"Total unique tools: {count}")
                if count >= 740:
                    print(f"Milestone 740 REACHED (Total: {count}).")
                else:
                    print(f"Milestone 740 NOT REACHED. Current count: {count}")
                    sys.exit(1)

    except Exception as e:
        print(f"Verification Error: {e}")
        sys.exit(1)

    print("\nSUPREME APEX VERIFICATION v780: SUCCESS")

if __name__ == "__main__":
    asyncio.run(verify())