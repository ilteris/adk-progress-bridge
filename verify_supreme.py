import subprocess
import sys
import os
import time

def run_command(command, cwd=None, env=None):
    print(f"\n>>> Running: {command}")
    result = subprocess.run(command, shell=True, cwd=cwd, env=env)
    if result.returncode != 0:
        print(f"!!! Command failed with exit code {result.returncode}")
        return False
    return True

def main():
    print("=== ADK PROGRESS BRIDGE SUPREME VERIFICATION (v300) ===")
    
    # 1. Backend Tests
    if not run_command("./venv/bin/python -m pytest tests/"):
        sys.exit(1)
        
    # 2. Frontend Unit Tests
    if not run_command("npm test -- --run", cwd="frontend"):
        sys.exit(1)
        
    # 3. Manual Verification Scripts
    if not run_command("./venv/bin/python verify_websocket.py && ./venv/bin/python backend/verify_docs.py && ./venv/bin/python verify_stream.py"):
        sys.exit(1)
        
    # 4. E2E Tests (Playwright)
    # We need to ensure the backend is NOT running on 8000 already, or just let Playwright handle it.
    # Actually, Playwright config has reuseExistingServer: true, so it's fine.
    if not run_command("npx playwright test", cwd="frontend"):
        sys.exit(1)
        
    print("\n=== ALL VERIFICATIONS PASSED: ABSOLUTE APEX ATTAINED (v300) ===")

if __name__ == "__main__":
    main()

