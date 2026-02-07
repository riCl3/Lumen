import requests
import sys
import os

BASE_URL = "http://localhost:8001"

print(f"Testing {BASE_URL}/api/browse...")

try:
    # 1. Test Root Listing
    resp = requests.get(f"{BASE_URL}/api/browse")
    if resp.status_code != 200:
        print(f"FAIL: Root listing failed: {resp.status_code} {resp.text}")
        sys.exit(1)
    
    roots = resp.json()
    print(f"Roots found: {len(roots)}")
    if len(roots) == 0:
        print("FAIL: No roots found")
        sys.exit(1)
    
    # 2. Test Directory Listing (current dir)
    cwd = os.getcwd()
    print(f"Testing directory listing for: {cwd}")
    resp = requests.get(f"{BASE_URL}/api/browse", params={"path": cwd})
    if resp.status_code != 200:
        print(f"FAIL: Directory listing failed: {resp.status_code} {resp.text}")
        sys.exit(1)
        
    items = resp.json()
    print(f"Items found: {len(items)}")
    
    # Verify we see valid items
    filenames = [i['name'] for i in items]
    if "server.py" not in filenames and "static" not in filenames:
         print(f"FAIL: Expected files not found in listing. Got: {filenames[:5]}...")
         sys.exit(1)

    print("PASS: File browser API seems functional.")

except Exception as e:
    print(f"FAIL: Exception: {e}")
    sys.exit(1)
