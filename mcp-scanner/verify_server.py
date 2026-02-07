import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def wait_for_server(url, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            requests.get(url)
            return True
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    return False

print("Waiting for server...")
if not wait_for_server(BASE_URL):
    print("Server failed to start.")
    sys.exit(1)

print("Server is up!")

# Test 1: Get Models
print("Testing /api/models...")
try:
    resp = requests.get(f"{BASE_URL}/api/models")
    resp.raise_for_status()
    models = resp.json()
    print(f"Models retrieved: {len(models)}")
    if len(models) == 0:
        print("FAIL: No models returned")
        sys.exit(1)
except Exception as e:
    print(f"FAIL: /api/models error: {e}")
    sys.exit(1)

# Test 2: Run Scan (Self-scan)
# We scan the current directory. It should work (fallback to static)
print("Testing /api/scan...")
try:
    # Use absolute path for safety
    import os
    cwd = os.getcwd()
    resp = requests.post(f"{BASE_URL}/api/scan", json={"path": cwd})
    if resp.status_code != 200:
        print(f"FAIL: /api/scan returned {resp.status_code}: {resp.text}")
        sys.exit(1)
    
    data = resp.json()
    print("Scan successful!")
    print(f"Total servers found: {data.get('total_servers_found')}")
    # We should find at least something (maybe scanner package itself isn't a server, but safe to check)
    # Actually, discovery looks for specific patterns. It might not find anything if this repo isn't an MCP server itself.
    # But as long as it returns 200 and a valid JSON structure, we are good.
    if "summary_statistics" not in data:
         print("FAIL: missing summary_statistics")
         sys.exit(1)
    
except Exception as e:
    print(f"FAIL: /api/scan error: {e}")
    sys.exit(1)

print("ALL TESTS PASSED")
