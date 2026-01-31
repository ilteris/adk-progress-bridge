import subprocess
import sys
import os
import time
import requests
import signal

def run_command(command, cwd=None, env=None):
    print(f"\n>>> Running: {command}")
    result = subprocess.run(command, shell=True, cwd=cwd, env=env)
    if result.returncode != 0:
        print(f"!!! Command failed with exit code {result.returncode}")
        return False
    return True

def wait_for_server(url, timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                print(f"Server is up at {url}")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    return False

def main():
    print("=== ADK PROGRESS BRIDGE SUPREME VERIFICATION (v303) ===")
    
    # 1. Backend Tests (unit/integration via pytest)
    if not run_command("./venv/bin/python -m pytest tests/"):
        sys.exit(1)
        
    # 2. Frontend Unit Tests (vitest)
    if not run_command("npm test -- --run", cwd="frontend"):
        sys.exit(1)
        
    # 3. Start Backend for manual scripts and E2E
    print("\n>>> Starting backend server for manual and E2E tests...")
    # Use the venv python to run uvicorn
    # Need to set PYTHONPATH to include backend directory
    env = os.environ.copy()
    env["PYTHONPATH"] = "backend"
    
    backend_proc = subprocess.Popen(
        ["./venv/bin/python", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid
    )
    
    try:
        if not wait_for_server("http://127.0.0.1:8000/tools"):
            print("!!! Backend failed to start")
            backend_proc.terminate()
            sys.exit(1)
            
        # 4. Manual Verification Scripts
        if not run_command("./venv/bin/python verify_websocket.py && ./venv/bin/python backend/verify_docs.py && ./venv/bin/python verify_stream.py"):
            backend_proc.terminate()
            sys.exit(1)
            
        # 5. E2E Tests (Playwright)
        if not run_command("npx playwright test", cwd="frontend"):
            backend_proc.terminate()
            sys.exit(1)
            
    finally:
        print("\n>>> Shutting down backend server...")
        os.killpg(os.getpgid(backend_proc.pid), signal.SIGTERM)
        backend_proc.wait()

    print("\n=== ALL VERIFICATIONS PASSED: SUPREME ABSOLUTE APEX ATTAINED (v303) ===")

if __name__ == "__main__":
    main()
