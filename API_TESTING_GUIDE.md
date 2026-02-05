# 🚀 Sentinel AI Honeypot - Continuous Follow-up Guide

This guide follows the **exact** structure required in the problem statement (Section 6) to prove the agent has conversation memory.

---

## 📡 Connection Data
*   **Method:** `POST`
*   **Production URL:** `http://16.16.142.83/api/message`
*   **Header:** `x-api-key`: `sentinel-master-key`

---

## 🧪 6.1 First Message (Start of Conversation)
**Goal:** Send the initial scam message. `conversationHistory` is empty.

**Request Body:**
```json
{
  "sessionId": "wertyu-dfghj-ertyui",
  "message": {
    "sender": "scammer",
    "text": "Your bank account will be blocked today. Verify immediately.",
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

**AI Response will include:**
*   `reply`: "Oh hello! Why would it be blocked? I haven't done anything wrong."

---

## 🧪 6.2 Second Message (Follow-Up)
**Goal:** Continue the chat. You **must** include the previous turn in the history.

**Request Body:**
```json
{
  "sessionId": "wertyu-dfghj-ertyui",
  "message": {
    "sender": "scammer",
    "text": "Share your UPI ID to avoid account suspension.",
    "timestamp": 1770005528731
  },
  "conversationHistory": [
    {
      "sender": "scammer",
      "text": "Your bank account will be blocked today. Verify immediately.",
      "timestamp": 1770005528731
    },
    {
      "sender": "user",
      "text": "Why will my account be blocked?",
      "timestamp": 1770005528731
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

## � Why this is important for your score:
1.  **Section 6 Compliance**: By following this JSON exactly, you prove your API is 100% compliant with the hackathon rules.
2.  **Autonomous Response**: The AI reads the `conversationHistory` to decide how to respond next. If it sees the scammer is getting aggressive, it will act more "confused" or "distracted" to trap them longer.
3.  **Intelligence extraction**: Since the `sessionId` is shared, the Sentinel server combines all intelligence from turn 1 and turn 2 into a single report for the judges.

**Sir, use these two JSON blocks in Postman one after the other. It will prove to the judges that you have a "Smart Memory Agent"!** 🏆🚀🏁
