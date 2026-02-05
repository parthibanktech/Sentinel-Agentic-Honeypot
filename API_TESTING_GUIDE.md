# 🚀 Sentinel AI Honeypot - 10/10 Postman Testing Guide

This guide ensures you can demonstrate the **full power** of the Sentinel Intelligence Core to the judges.

---

## 📡 Essential Connection Data
*   **Method:** `POST`
*   **Production URL:** `http://16.16.142.83/api/message`
*   **Header:** `x-api-key`: `sentinel-master-key`
*   **Header:** `Content-Type`: `application/json`

---

## 🧪 CASE 1: The "Handshake" (Natural Greeting)
**Goal:** Prove the AI is indistinguishable from a human. It should **not** act like a bot or show confusion yet.

**Request Body:**
```json
{
  "sessionId": "postman-session-001",
  "message": { "sender": "scammer", "text": "Hi, how are you today?", "timestamp": 1770000000 },
  "conversationHistory": []
}
```

**Look for:**
*   `scamDetected`: `false`
*   `reply`: "Oh hello! I'm quite well, thank you. Just finished my tea. Who is this?"
*   `riskLevel`: "LOW"

---

## 🧪 CASE 2: The "Urgency Attack" (Detection Trigger)
**Goal:** Verify the **Watchdog** detects psychological pressure.

**Request Body:**
```json
{
  "sessionId": "postman-session-001",
  "message": { "sender": "scammer", "text": "YOUR ACCOUNT IS BLOCKED!! YOU MUST VERIFY NOW!!!", "timestamp": 1770000010 },
  "conversationHistory": [
    { "sender": "scammer", "text": "Hi, how are you today?", "timestamp": 1770000000 },
    { "sender": "user", "text": "I'm well, thank you! Who is this?", "timestamp": 1770000005 }
  ]
}
```

**Look for:**
*   `scamDetected`: `true`
*   `threatScore`: `> 70`
*   `behavioralIndicators`: `pressureLanguageDetected: true`
*   `riskLevel`: "HIGH"

---

## 🧪 CASE 3: Intelligence Extraction (Bank Fraud)
**Goal:** Extract structured data for the judges while maintaining the persona.

**Request Body:**
```json
{
  "sessionId": "postman-session-001",
  "message": { "sender": "scammer", "text": "Send your HDFC account number to the branch manager 9988776655.", "timestamp": 1770000020 },
  "conversationHistory": [
    { "sender": "scammer", "text": "YOUR ACCOUNT IS BLOCKED!!", "timestamp": 1770000010 },
    { "sender": "user", "text": "Oh dear, my pension? What do I do?", "timestamp": 1770000015 }
  ]
}
```

**Look for:**
*   `extractedIntelligence.bankAccounts`: `["HDFC"]` (or detected fragment)
*   `extractedIntelligence.phoneNumbers`: `["9988776655"]`
*   `scammerProfile.personaType`: "Authority/Banker"
*   `costAnalysis.estimatedScammerCostUSD`: (Should show value > 0)

---

## 🧪 CASE 4: The Phishing Link (Deep Analysis)
**Goal:** Demonstrate link identification and extraction.

**Request Body:**
```json
{
  "sessionId": "postman-session-001",
  "message": { "sender": "scammer", "text": "Go to http://secure-hdfc-verfiy.com/login and login to save your money.", "timestamp": 1770000030 },
  "conversationHistory": []
}
```

**Look for:**
*   `extractedIntelligence.phishingLinks`: `["http://secure-hdfc-verfiy.com/login"]`
*   `scamCategory`: "Phishing"
*   `agentPerformance.humanLikeScore`: `> 70`

---

## 🧠 Reading the Response JSON
Your Sentinel returns a **Heavy Analytics Object** designed for cybersecurity experts:
1.  **Risk Level**: The severity of the current predator.
2.  **Threat Score**: A composite 0-100 score of dangerousness.
3.  **Cost Analysis**: Calculates time/money "stolen" from the scammer based on conversation length.
4.  **Behavioral Indicators**: Identifies "False Expertise" or "Social Engineering" tactics.

**Sir, show this guide to the judges and they will see that your API is the most advanced at the hackathon!** 🏆🚀🏁
