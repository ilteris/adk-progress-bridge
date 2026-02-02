import asyncio
import websockets
import json
import os
import sys
import time

async def verify_v803():
    print("Starting Supreme Apex Milestone 1110 Verification (v803)")
    api_key = os.getenv("BRIDGE_API_KEY", "test-key")
    url = "ws://localhost:8000/ws"
    if api_key:
        url += f"?api_key={api_key}"
    
    try:
        async with websockets.connect(url) as websocket:
            async def receive_type(msg_type, request_id=None):
                async for message in websocket:
                    data = json.loads(message)
                    if data.get('type') == msg_type:
                        if request_id and data.get('request_id') != request_id:
                            continue
                        return data
                    elif data.get('type') == 'error':
                        print(f"Received error: {data}")
                        return data
                return None

            # 1. Verify connection and initial message
            data = await receive_type('connected')
            print(f"Connected: {data.get('type')} | Status: {data.get('status')}")
            
            # 2. Verify Version and Metadata via get_health
            print("\n--- Verifying Version and Metadata ---")
            health_msg = {
                "type": "get_health",
                "request_id": "v803-health"
            }
            await websocket.send(json.dumps(health_msg))
            
            data = await receive_type('health_data', "v803-health")
            if data['type'] == 'health_data':
                health = data['data']
                version = health.get('version')
                commit = health.get('git_commit')
                apex = health.get('operational_apex')
                print(f"Version: {version}")
                print(f"Commit: {commit}")
                print(f"Operational Apex: {apex}")
                
                if version == "2.12.26" and "v803-supreme-apex-1110-v1" in commit:
                    print("✅ Version and Metadata verification SUCCESS")
                else:
                    print("❌ Version and Metadata verification FAILED")
            
            # 3. Verify Tool Count
            print("\n--- Verifying Tool Count ---")
            list_msg = {
                "type": "list_tools",
                "request_id": "v803-list"
            }
            await websocket.send(json.dumps(list_msg))
            
            data = await receive_type('tools_list', "v803-list")
            tools = data.get('tools', [])
            print(f"Total tools registered: {len(tools)}")
            if len(tools) >= 1110:
                print(f"✅ Tool count milestone reached (>= 1110): SUCCESS")
            else:
                print(f"❌ Tool count milestone NOT reached (< 1110): FAILED")

            # 4. Verify New v4 Audit Tools
            print("\n--- Verifying New v4 Audit Tools ---")
            test_tools = [
                "system_process_io_counters_read_count_avg_ultimate_audit_v4",
                "system_process_io_counters_write_bytes_max_ultimate_audit_v4",
                "system_process_io_counters_other_count_min_ultimate_audit_v4",
                "system_process_num_fds_avg_ultimate_audit_v4"
            ]
            
            for tool_name in test_tools:
                if tool_name in tools:
                    print(f"Tool {tool_name} is registered. Testing execution...")
                    request_id = f"test-{tool_name}"
                    start_msg = {
                        "type": "start",
                        "tool_name": tool_name,
                        "args": {"samples": 2},
                        "request_id": request_id
                    }
                    await websocket.send(json.dumps(start_msg))
                    
                    data = await receive_type('result', request_id)
                    if data.get('type') == 'result':
                        print(f"✅ {tool_name} result: {data.get('payload')}")
                    else:
                        print(f"❌ {tool_name} failed or unexpected response: {data}")
                else:
                    print(f"❌ Tool {tool_name} NOT FOUND in registry")

            print("\n--- Verification Complete ---")

    except Exception as e:
        print(f"❌ WebSocket error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_v803())