import requests
import json
import time

def check_version():
    print("\n--- Checking Version ---")
    try:
        resp = requests.get("http://localhost:8000/version")
        print(json.dumps(resp.json(), indent=2))
    except Exception as e:
        print(f"Failed to check version: {e}")

def test_tool(tool_name, args={}):
    print(f"\n--- Testing Tool: {tool_name} with args: {args} ---")
    try:
        resp = requests.post(f"http://localhost:8000/start_task/{tool_name}", json={"args": args})
        if resp.status_code != 200:
            print(f"Failed to start task: {resp.text}")
            return
        
        call_id = resp.json()["call_id"]
        print(f"Task started. Call ID: {call_id}")
        
        stream_resp = requests.get(f"http://localhost:8000/stream/{call_id}", stream=True)
        
        for line in stream_resp.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data: "):
                    try:
                        data = json.loads(decoded_line[6:])
                        payload = data['payload']
                        if data['type'] == 'progress':
                            print(f"[{payload.get('pct')}%] {payload.get('step')}: {payload.get('log')}")
                        elif data['type'] == 'result':
                            print(f"RESULT: {json.dumps(payload, indent=2)}")
                        elif data['type'] == 'system_metrics':
                            pass # Too noisy
                        elif data['type'] == 'error':
                            print(f"ERROR: {payload}")
                    except Exception as e:
                        print(f"Error parsing line: {e}")
    except Exception as e:
        print(f"Error testing tool: {e}")

if __name__ == "__main__":
    check_version()
    test_tool("system_swap_memory_sin_total_audit")
    test_tool("system_swap_memory_sout_total_audit")
    test_tool("system_net_io_dropout_total_audit")
