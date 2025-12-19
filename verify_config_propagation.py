import requests
import time
import json
import hmac
import hashlib

# Localhost URL
BASE_URL = "http://localhost:5002"
API_URL = f"{BASE_URL}/api/plugin"
API_KEY = "ak-64c82d1634cb4a52"
API_SECRET = "as-83a51f676f014778bb081b97ed716460"

def sign_request(body):
    timestamp = str(int(time.time()))
    body_bytes = json.dumps(body, separators=(',', ':')).encode('utf-8')
    parts = [body_bytes, timestamp.encode('utf-8')]
    message = b''.join(parts)
    signature = hmac.new(API_SECRET.encode('utf-8'), message, hashlib.sha256).hexdigest()
    return {
        'D-API-KEY': API_KEY,
        'D-TIMESTAMP': timestamp,
        'D-SIGNATURE': signature,
        'Content-Type': 'application/json'
    }, body_bytes

def test_config_propagation():
    print("Testing Config Propagation...")
    config_payload = {"query": "cats"}
    body = {
        "subtask_id": "test-propagate-1",
        "config": config_payload,
        "input_files": []
    }
    headers, body_bytes = sign_request(body)
    try:
        resp = requests.post(f"{API_URL}/create_task", data=body_bytes, headers=headers)
        print(f"Status: {resp.status_code}")
        print("Check backend logs for: [DEBUG] Received config: {'query': 'cats'}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_config_propagation()
