import requests
import json
import time

URL = "http://localhost:8000/api/message"
HEADERS = {
    "x-api-key": "sentinel-master-key",
    "Content-Type": "application/json"
}

def test_api():
    print("--- Test 1: First Message ---")
    payload1 = {
        "sessionId": "test-session-123",
        "message": {
            "sender": "scammer",
            "text": "URGENT: Your SBI account is blocked. Verify at http://fake-sbi.com now!",
            "timestamp": int(time.time() * 1000)
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    try:
        resp1 = requests.post(URL, headers=HEADERS, json=payload1)
        print(f"Status: {resp1.status_code}")
        print(f"Response: {json.dumps(resp1.json(), indent=2)}")
        
        # Test 2: Follow up
        print("\n--- Test 2: Follow-up Message ---")
        payload2 = {
            "sessionId": "test-session-123",
            "message": {
                "sender": "scammer",
                "text": "Share your account number to unlock immediately.",
                "timestamp": int(time.time() * 1000)
            },
            "conversationHistory": [
                payload1["message"],
                {"sender": "user", "text": resp1.json().get("reply", ""), "timestamp": int(time.time() * 1000)}
            ],
            "metadata": payload1["metadata"]
        }
        
        resp2 = requests.post(URL, headers=HEADERS, json=payload2)
        print(f"Status: {resp2.status_code}")
        print(f"Response: {json.dumps(resp2.json(), indent=2)}")

    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: Make sure your server is running (python backend/server.py)")

if __name__ == "__main__":
    test_api()
