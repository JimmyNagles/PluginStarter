import socket

TARGET_IP = "43.134.209.46"
PORTS_TO_CHECK = [80, 443, 5000, 5001, 8000, 8080, 8081, 3000]

def check_port(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2.0)
    result = sock.connect_ex((ip, port))
    sock.close()
    return result == 0

print(f"Scanning {TARGET_IP} for open DataHub ports...")
found = False
for port in PORTS_TO_CHECK:
    print(f"Checking port {port}...", end=" ", flush=True)
    if check_port(TARGET_IP, port):
        print("OPEN! ✅")
        print(f"\n>>> FOUND OPEN PORT: {port}")
        print(f">>> Try updating app.py DATAHUB_API_URL to: http://{TARGET_IP}:{port} (or https if 443)")
        found = True
        break
    else:
        print("Closed ❌")

if not found:
    print("\nNo common ports found open. You may need to ask the DataHub provider for the correct API URL.")
