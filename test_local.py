import requests
import time
import json
import hmac
import hashlib
import threading

# Localhost URL
BASE_URL = "http://localhost:5002"
API_URL = f"{BASE_URL}/api/plugin"

# Keys matching backend/app.py
API_KEY = "ak-64c82d1634cb4a52"
API_SECRET = "as-83a51f676f014778bb081b97ed716460"

def sign_request(body, params=None):
    timestamp = str(int(time.time()))
    body_bytes = json.dumps(body, separators=(',', ':')).encode('utf-8')
    
    parts = []
    if params:
         sorted_params = json.dumps(params, sort_keys=True, separators=(',', ':'))
         parts.append(sorted_params.encode('utf-8'))
    parts.append(body_bytes)
    parts.append(timestamp.encode('utf-8'))
    
    message = b''.join(parts)
    signature = hmac.new(API_SECRET.encode('utf-8'), message, hashlib.sha256).hexdigest()
    
    return {
        'D-API-KEY': API_KEY,
        'D-TIMESTAMP': timestamp,
        'D-SIGNATURE': signature,
        'Content-Type': 'application/json'
    }, body_bytes

def test_health():
    print(f"[{threading.current_thread().name}] Testing /health...")
    ts = str(int(time.time()))
    msg = b'' + ts.encode('utf-8')
    sig = hmac.new(API_SECRET.encode('utf-8'), msg, hashlib.sha256).hexdigest()
    headers = {'D-API-KEY': API_KEY, 'D-TIMESTAMP': ts, 'D-SIGNATURE': sig}
    try:
        r = requests.get(f"{API_URL}/health", headers=headers)
        print(f"Health: {r.status_code}")
    except Exception as e:
        print(f"Health failed: {e}")

def create_task_request(subtask_id, config):
    print(f"[{threading.current_thread().name}] Creating task {subtask_id}...")
    body = {
        "subtask_id": subtask_id,
        "config": config,
        "input_files": []
    }
    headers, body_bytes = sign_request(body)
    try:
        resp = requests.post(f"{API_URL}/create_task", data=body_bytes, headers=headers)
        print(f"[{subtask_id}] Status: {resp.status_code}, Body: {resp.json()}")
    except Exception as e:
        print(f"[{subtask_id}] Failed: {e}")

def test_concurrency():
    print("\n--- Testing Concurrency ---")
    t1 = threading.Thread(target=create_task_request, args=("task-parallel-1", {"keyword": "A"}))
    t2 = threading.Thread(target=create_task_request, args=("task-parallel-2", {"keyword": "B"}))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

def test_failure():
    print("\n--- Testing Failure Reporting ---")
    create_task_request("task-fail-1", {"force_fail": True})

def test_idempotency():
    print("\n--- Testing Idempotency ---")
    create_task_request("task-idem-1", {"keyword": "First"})
    time.sleep(0.5)
    create_task_request("task-idem-1", {"keyword": "Second"})

if __name__ == "__main__":
    test_health()
    test_concurrency()
    test_failure()
    test_idempotency()
