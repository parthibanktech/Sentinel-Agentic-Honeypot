# 🚀 Sentinel AI Honeypot - API Testing Guide (Postman)

Use this guide to test your backend API directly. This bypasses the frontend and confirms that your **Autonomous Agent** and **Intelligence Extraction** are working according to the Hackathon requirements.

---

## 📡 API endpoint
*   **Method:** `POST`
*   **Production URL:** `http://16.16.142.83/api/message`
*   **Local URL:** `http://localhost:8000/api/message`

---

## 🔑 Required Headers
| Key | Value |
| :--- | :--- |
| `Content-Type` | `application/json` |
| `x-api-key` | `sentinel-master-key` |

---

## 🧪 Scenario 1: First Message (Handshake)
**Goal:** Test if the AI detects the scam and responds as the persona "Alex".

**Request Body:**
```json
{
  "sessionId": "test-session-001",
  "message": {
    "sender": "scammer",
    "text": "URGENT: Your HDFC bank account is frozen. Click http://bit.ly/verify-hdfc to unblock now.",
    "timestamp": 1770005528731
  },
  "conversationHistory": [],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

**What to look for in Response:**
1.  `status`: should be `"success"`
2.  `reply`: should be something like *"Oh dear, I don't understand these links. What is happening?"*
3.  `scamDetected`: should be `true`
4.  `confidenceScore`: should be `> 80`
5.  `extractedIntelligence`: should contain the `phishingLinks` and `suspiciousKeywords`.

---

## 🧪 Scenario 2: Intelligence Extraction (Follow-up)
**Goal:** Verify that the "Alex" persona traps the scammer into giving bank details.

**Request Body:**
```json
{
  "sessionId": "test-session-001",
  "message": {
    "sender": "scammer",
    "text": "I need your account number and OTP to process the refund.",
    "timestamp": 1770005529000
  },
  "conversationHistory": [
    {
      "sender": "scammer",
      "text": "URGENT: Your HDFC bank account is frozen.",
      "timestamp": 1770005528731
    },
    {
      "sender": "user",
      "text": "Oh dear, I'm so worried. My grandson usually helps with this.",
      "timestamp": 1770005528800
    }
  ],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

---

## 🧠 Why this is "Agentic"?
1.  **Autonomous Decision**: The AI decides *not* to tell the scammer it has detected them.
2.  **Intelligence extraction**: It saves all links and accounts into the `extractedIntelligence` object.
3.  **Final Callback**: Behind the scenes, the server automatically POSTs this data to `hackathon.guvi.in` once `scamDetected` is true.

---

## 🛠️ Still seeing "Grandson" fallback?
If you see the message about "Grandson helping me" every time, it means the **OpenAI Key** on the server is either:
1.  **Missing** (Check the `.env` file on the server)
2.  **Out of Credits** (Check OpenAI dashboard)
3.  **Invalid**

*Note: The Sentinel is now using the 'Heuristic Watchdog', so it will still flag the scam even if the AI is offline!*
