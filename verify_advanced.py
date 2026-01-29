import requests
import json
import time
import sys

def test_tool(tool_name, args={}):
    print(f"\n--- Testing Tool: {tool_name} with args: {args} ---")
    # 1. Start Task
    # WRONG: resp = requests.post(f"http://localhost:8000/start_task/{tool_name}", json=args)
    # CORRECT: TaskStartRequest has an 'args' field
    resp = requests.post(f"http://localhost:8000/start_task/{tool_name}", json={"args": args})
    
    if resp.status_code != 200:
        print(f"Failed to start task: {resp.text}")
        return
    
    call_id = resp.json()["call_id"]
    print(f"Task started. Call ID: {call_id}")
    
    # 2. Stream
    stream_resp = requests.get(f"http://localhost:8000/stream/{call_id}", stream=True)
    
    for line in stream_resp.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith("data: "):
                data = json.loads(decoded_line[6:])
                payload = data['payload']
                if data['type'] == 'progress':
                    print(f"[{payload.get('pct')}%] {payload.get('step')}: {payload.get('log')}")
                elif data['type'] == 'result':
                    print(f"RESULT: {payload}")
                elif data['type'] == 'error':
                    print(f"ERROR: {payload}")

if __name__ == "__main__":
    test_tool("multi_stage_analysis", {"documents": 1})
    test_tool("parallel_report_generation", {"reports": 2})
    test_tool("brittle_process", {"fail_at": 30})
