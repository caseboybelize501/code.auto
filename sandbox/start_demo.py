"""
Sandbox Interactive Demo Launcher

Run this to start the sandbox server and test it interactively.
"""

import subprocess
import sys
import time
import requests
import json

def main():
    print("=" * 70)
    print("32-THREAD SANDBOX - INTERACTIVE DEMO")
    print("=" * 70)
    print()
    
    # Start server in background
    print("Starting sandbox server...")
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7332"],
        cwd="d:\\Users\\CASE\\projects\\code.auto\\sandbox",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Wait for server to start
    print("Waiting for server to initialize (up to 15 seconds)...")
    for i in range(15):
        time.sleep(1)
        try:
            r = requests.get("http://localhost:7332/health", timeout=2)
            if r.status_code == 200:
                print(f"\n[OK] Server is running!\n")
                break
        except:
            print(f"  Waiting... ({i+1}s)")
    else:
        print("\n[ERROR] Server failed to start. Check output below:")
        print("=" * 70)
        return
    
    # Show server info
    print("=" * 70)
    print("SERVER INFO")
    print("=" * 70)
    
    # Health check
    r = requests.get("http://localhost:7332/health")
    print(f"Health: {json.dumps(r.json(), indent=2)}")
    
    # Get stats
    r = requests.get("http://localhost:7332/stats")
    print(f"\nStats: {json.dumps(r.json(), indent=2)}")
    
    print("\n" + "=" * 70)
    print("TEST EXECUTION")
    print("=" * 70)
    
    # Test Python execution
    print("\n1. Testing Python execution...")
    r = requests.post("http://localhost:7332/execute", json={
        "code": "print('Hello from the 32-thread sandbox!')",
        "language": "python",
        "timeout": 5
    })
    print(f"   Response: {json.dumps(r.json(), indent=2)}")
    
    # Test Node.js execution
    print("\n2. Testing Node.js execution...")
    r = requests.post("http://localhost:7332/execute", json={
        "code": "console.log('Node.js is working!')",
        "language": "node",
        "timeout": 5
    })
    print(f"   Response: {json.dumps(r.json(), indent=2)}")
    
    # Test code validation
    print("\n3. Testing code validation...")
    r = requests.post("http://localhost:7332/validate", json={
        "prompt": "Print hello world",
        "code": "print('Hello, World!')",
        "expected_output": "Hello, World!",
        "timeout": 5
    })
    print(f"   Response: {json.dumps(r.json(), indent=2)}")
    
    print("\n" + "=" * 70)
    print("API ENDPOINTS")
    print("=" * 70)
    print("""
Execute Code:
  POST http://localhost:7332/execute
  Body: {"code": "print('hi')", "language": "python", "timeout": 5}

Validate Code:
  POST http://localhost:7332/validate
  Body: {"prompt": "...", "code": "...", "expected_output": "..."}

Get Statistics:
  GET http://localhost:7332/stats

Get Topology:
  GET http://localhost:7332/topology

API Docs:
  GET http://localhost:7332/docs
""")
    
    print("=" * 70)
    print("Server is running! Press Ctrl+C to stop.")
    print("=" * 70)
    
    # Keep server running
    try:
        server_proc.wait()
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        server_proc.terminate()
        print("Server stopped.")


if __name__ == "__main__":
    main()
