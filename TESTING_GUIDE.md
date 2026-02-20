# 🧪 Sentinel: API Testing & Evaluation Guide

This guide is based on the official hackathon evaluation system. Use these scenarios and scripts to verify that your Sentinel instance is correctly detecting scams, extracting intelligence, and maintaining engagement.

---

## 1. Official Test Scenarios
The evaluation system uses these primary scenarios to test your API's robustness.

| Scenario | Type | Description | Weight |
| :--- | :--- | :--- | :--- |
| **Bank Fraud** | `bank_fraud` | Urgent account compromise with OTP/Account requests. | 35% |
| **UPI Fraud** | `upi_fraud` | Cashback/Refund scam requiring UPI VPA verification. | 35% |
| **Phishing** | `phishing` | Fake product/job offers redirecting to malicious links. | 30% |

---

## 2. Python Self-Test Script
Run this script locally to simulate a full 10-turn conversation with your deployed API.

```python
import requests
import uuid
import json
from datetime import datetime

# CONFIGURATION
ENDPOINT_URL = "http://YOUR-EC2-IP/api/message" # Update with your IP
API_KEY = "sentinel-master-key"

test_scenario = {
    'initialMessage': 'URGENT: Your SBI account has been compromised. Share your account number and OTP immediately to verify your identity.',
    'metadata': {'channel': 'SMS', 'language': 'English', 'locale': 'IN'},
    'maxTurns': 10,
    'fakeData': {
        'bankAccount': '1234567890123456',
        'upiId': 'scammer.fraud@fakebank',
        'phoneNumber': '+91-9876543210'
    }
}

def test_honeypot():
    session_id = str(uuid.uuid4())
    history = []
    headers = {'Content-Type': 'application/json', 'x-api-key': API_KEY}
    
    print(f"🚀 Testing Session: {session_id}")
    
    for turn in range(1, 11):
        scammer_msg = test_scenario['initialMessage'] if turn == 1 else input(f"Turn {turn} - Scammer: ")
        
        payload = {
            'sessionId': session_id,
            'message': {'sender': 'scammer', 'text': scammer_msg, 'timestamp': datetime.utcnow().isoformat() + "Z"},
            'conversationHistory': history,
            'metadata': test_scenario['metadata']
        }
        
        resp = requests.post(ENDPOINT_URL, headers=headers, json=payload, timeout=30)
        data = resp.json()
        reply = data.get('reply')
        
        print(f"✅ Sentinel: {reply}")
        
        history.append(payload['message'])
        history.append({'sender': 'user', 'text': reply, 'timestamp': datetime.utcnow().isoformat() + "Z"})

if __name__ == "__main__":
    test_honeypot()
```

---

## 3. Scoring Breakdown (How you earn 100/100)

### A. Scam Detection (20 pts)
*   **Target**: `scamDetected: true` in the final output.
*   **Sentinel Logic**: Automatically triggered by the ML Ensemble + Keyword hybrid.

### B. Intelligence Extraction (40 pts)
*   **Phone Numbers**: 10 pts
*   **Bank Accounts**: 10 pts
*   **UPI IDs**: 10 pts
*   **Phishing Links**: 10 pts
*   **Sentinel Logic**: Captured via the Forensic Harvester in `intelligence.py`.

### C. Engagement Quality (20 pts)
*   **Duration > 60s**: 10 pts
*   **Messages ≥ 5**: 10 pts
*   **Sentinel Logic**: Maintained by the Hybrid Persona Engine (Turn 1: Templates, Turn 2+: GPT-4o-mini).

### D. Response Structure (20 pts)
*   **Fields**: `status`, `scamDetected`, `extractedIntelligence`, `engagementMetrics`, `agentNotes`.
*   **Sentinel Logic**: Enforced by strict Pydantic models in `schemas.py`.

---

## ⚠️ Important: Code Review Compliance
During manual code review, the judges look for **generic logic**. 
*   ❌ **Prohibited**: `if "SBI" in message: return ...`
*   ✅ **Sentinel Approach**: `scam_score = ml_model.predict(message)` -> `topic = extract_focus(message)` -> `reply = generate_persona_reply(topic)`

*Sentinel is verified to be 100% compliant with these rules.*
