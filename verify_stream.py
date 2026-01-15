import requests
import json
import time

def test_stream():
    # 1. Start Task
    print("Starting task...")
    resp = requests.post("http://localhost:8000/start_task/long_audit", json={"duration": 2})
    if resp.status_code != 200:
        print(f"Failed to start task: {resp.text}")
        return
    
    call_id = resp.json()["call_id"]
    print(f"Task started. Call ID: {call_id}")
    
    # 2. Stream
    print("Streaming events...")
    stream_resp = requests.get(f"http://localhost:8000/stream/{call_id}", stream=True)
    
    for line in stream_resp.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith("data: "):
                data = json.loads(decoded_line[6:])
                print(f"Event: {data['type']} | {data['payload']}")

if __name__ == "__main__":
    test_stream()
