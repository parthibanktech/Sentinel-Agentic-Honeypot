import requests, json, time

URL = 'http://localhost:8080/api/message'
H = {'Content-Type': 'application/json', 'x-api-key': 'sentinel-master-key'}
SID = f'speed-{int(time.time())}'

tests = [
    ('Greeting', 'Hi'),
    ('Bank Fraud', 'This is SBI fraud department. Your account ending in 4432 has been compromised. Call +91-9876543210 immediately.'),
    ('Phishing', 'URGENT: Click http://bit.ly/sbi-verify to verify your KYC or your account will be blocked in 24 hours.'),
    ('UPI', 'To unblock, send Rs.500 to verify@okaxis via UPI. Your reference number is REF-887766.'),
    ('OTP', 'I am sending OTP to your registered mobile. Please share the 6-digit code for verification.'),
    ('Job Scam', 'Hello dear, part time job offer. Earn 5000-8000 daily working from home. Message me on WhatsApp +919876543210.'),
    ('Lottery', 'Congratulations! You won 1 Crore in KBC Lottery. Deposit processing fee of 5000 to UPI ID kbcwinner@okaxis.'),
    ('Police', 'This is CBI calling. There is an arrest warrant against you. Your Aadhaar has been used for money laundering.'),
    ('Follow up', 'Why are you not responding? Your account will be permanently blocked in 1 hour.'),
    ('Closing', 'Ok fine. Last chance. Send money to 1234567890123456 HDFC account or face legal action.'),
]

lines = []
total = 0
for i, (desc, txt) in enumerate(tests):
    body = {'sessionId': SID, 'message': {'sender': 'scammer', 'text': txt, 'timestamp': int(time.time()*1000)}, 'conversationHistory': [], 'metadata': {'channel': 'SMS', 'language': 'English', 'locale': 'IN'}}
    t = time.time()
    r = requests.post(URL, json=body, headers=H, timeout=30)
    e = time.time() - t
    total += e
    d = r.json()
    tag = 'FAST' if e < 2.0 else ('OK' if e < 5.0 else 'SLOW')
    lines.append(f'T{i+1:2d} {desc:12s} | {e:.2f}s [{tag:4s}] | {d.get("reply","")[:70]}')

lines.append(f'---')
lines.append(f'Total: {total:.2f}s | Avg: {total/len(tests):.2f}s per turn')
fast = sum(1 for l in lines if '[FAST]' in l)
ok = sum(1 for l in lines if '[OK  ]' in l)
lines.append(f'FAST(<2s): {fast} | OK(<5s): {ok} | Total under 5s: {fast+ok}/{len(tests)}')

output = '\n'.join(lines)
with open('backend/speed_results.txt', 'w', encoding='utf-8') as f:
    f.write(output)
print(output)
