"""
Test that log buffer is being populated
"""
import requests
import time

base_url = "http://localhost:8000"

print("Testing log buffer...")

# First, trigger some logs
print("\n1. Adding test logs...")
response = requests.post(f"{base_url}/api/test-logs")
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Wait a moment
time.sleep(1)

# Now check if logs are in the buffer
print("\n2. Fetching logs from buffer...")
response = requests.get(f"{base_url}/api/logs")
print(f"Status: {response.status_code}")
data = response.json()
print(f"Logs in buffer: {len(data.get('logs', []))}")

if data.get('logs'):
    print("\nLogs:")
    for log in data['logs']:
        print(f"  - {log}")
else:
    print("ERROR: No logs found in buffer!")
