import requests, time

URL = 'http://localhost:8080/api/message'
H = {'Content-Type': 'application/json', 'x-api-key': 'sentinel-master-key'}

# Single request benchmark
msg = 'Your SBI account is blocked. Call +91-9876543210 immediately.'
body = {'sessionId': 'bench-1', 'message': {'sender': 'scammer', 'text': msg, 'timestamp': 0}, 'conversationHistory': [], 'metadata': {'channel': 'SMS'}}

t = time.time()
r = requests.post(URL, json=body, headers=H, timeout=30)
e = time.time() - t

d = r.json()
print(f"Time: {e:.2f}s")
print(f"Reply: {d.get('reply','')}")
print(f"Status: {d.get('status','')}")
