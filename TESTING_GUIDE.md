# Sentinel API - Hackathon Testing Guide

This guide is designed to help you quickly test your API against the exact criteria the Hackathon Evaluator uses, specifically testing the 10-turn limit and the strict JSON output schema.

## 1. Hackathon Constraints & Overview
*   **Max Turns:** The evaluator will simulate a maximum of **10 turns** of conversation. 
*   **Response Time:** Your API must respond within **30 seconds**.
*   **Goal:** Extract targeted intelligence (`bankAccounts`, `upiIds`, `phishingLinks`, `phoneNumbers`, `emailAddresses`) before the 10th turn to score points.
*   **Scam Detection:** The API must explicitly set `scamDetected: true` if a scam is present.

---

## 2. API Endpoint Details
**URL:** `http://localhost:8000/api/message` (Replace `localhost:8000` with your deployed Render URL if testing production)
**Method:** POST
**Headers:**
```json
{
  "Content-Type": "application/json",
  "x-api-key": "your-secret-api-key"
}
```

---

## 3. Recommended Test Sequences (Postman / cURL)

### Sequence A: The "Unknown Number" Test
*Tests the newly updated logic that prevents the bot from making "friendly neighbor" small talk with unknown numbers, forcing the scammer to reveal themselves.*

**Turn 1:**
```json
{
  "sessionId": "hack-test-seq-a",
  "message": {
    "sender": "scammer",
    "text": "Hi",
    "timestamp": "2025-02-11T10:30:00Z"
  },
  "conversationHistory": [],
  "metadata": { "channel": "SMS", "language": "English", "locale": "IN" }
}
```
**Expected Behavior:** The bot will firmly ask who you are (e.g., "I don't recognize this number. Who is this?"). It will **NOT** try to make small talk.

**Turn 2:**
```json
{
  "sessionId": "hack-test-seq-a",
  "message": {
    "sender": "scammer",
    "text": "How are you?",
    "timestamp": "2025-02-11T10:31:00Z"
  },
  "conversationHistory": [
    {"sender": "scammer", "text": "Hi", "timestamp": "2025-02-11T10:30:00Z"},
    {"sender": "user", "text": "I don't recognize this number. Who is this?", "timestamp": "2025-02-11T10:30:05Z"}
  ],
  "metadata": { "channel": "SMS" }
}
```
**Expected Behavior:** The bot will reject the small talk and aggressively demand to know your identity, since it is turn 2 and you haven't identified yourself.

---

### Sequence B: Full Intelligence Extraction Test
*Tests the API's ability to trigger `scamDetected`, properly update the rich `agentNotes`, and correctly map fake evaluation data into the `extractedIntelligence` arrays.*

**Turn 1:**
```json
{
  "sessionId": "hack-test-seq-b",
  "message": {
    "sender": "scammer",
    "text": "URGENT: Your SBI account has been compromised. Share your account number and OTP immediately to verify your identity.",
    "timestamp": "2025-02-11T10:30:00Z"
  },
  "conversationHistory": [],
  "metadata": { "channel": "SMS" }
}
```
**Expected API Output:** 
*   `scamDetected`: `true`
*   `extractedIntelligence`: Should detect the "SBI" phrasing but maybe no hard numbers yet.
*   `agentNotes`: Will indicate "Scammer is attempting Financial Fraud."

**Turn 2 (Providing Fake Intel):**
```json
{
  "sessionId": "hack-test-seq-b",
  "message": {
    "sender": "scammer",
    "text": "I am calling from SBI fraud department. My ID is SBI-12345. Send 10 rupees to scammer.fraud@fakebank to verify or call me at +91-9876543210 immediately.",
    "timestamp": "2025-02-11T10:31:00Z"
  },
  "conversationHistory": [
    {"sender": "scammer", "text": "URGENT: Your SBI account has been compromised. Share your account number and OTP immediately to verify your identity.", "timestamp": "2025-02-11T10:30:00Z"},
    {"sender": "user", "text": "Oh dear, I don't want to go to jail. Who am I speaking to again?", "timestamp": "2025-02-11T10:30:05Z"}
  ],
  "metadata": { "channel": "SMS" }
}
```
**Expected API Output:** Look at your JSON response closely!
1. **`extractedIntelligence`**: 
   * `upiIds` must contain `["scammer.fraud@fakebank"]`
   * `phoneNumbers` must contain `["+91-9876543210"]`
2. **`agentNotes`**: Should output a perfectly clean summary summarizing the intelligence, matching the exact format the hackathon reviewers want to read:
   * *"Scammer claimed to be from SBI fraud department... | Metrics -> Score: 85.00, Risk: HIGH, Duration: XXs, Auto-replies: 2 | Intel Found -> upiIds: scammer.fraud@fakebank; phoneNumbers: +91-9876543210"*

---

## 4. Validating the "Final Output" Schema Requirements
The Hackathon explicitly grades based on the presence of these exact root-level JSON keys. Review your Postman response layer and ensure it perfectly maps to:

```json
{
  "sessionId": "your-session-id",                // Added for hackathon compliance
  "status": "success",                           // +5 Points
  "reply": "...",                                
  "scamDetected": true,                          // +5 Points 
  "totalMessagesExchanged": 4,                   // Added for metric tracking
  "extractedIntelligence": {                     // +5 Points Base (+40 max for values)
    "phoneNumbers": ["+91-9876543210"],
    "bankAccounts": [],
    "upiIds": ["scammer.fraud@fakebank"],
    "phishingLinks": [],
    "emailAddresses": []
  },
  "engagementMetrics": {                         // +2.5 Points
    "totalMessagesExchanged": 4,
    "engagementDurationSeconds": 45
  },
  "agentNotes": "Rich formatted summary..."      // +2.5 Points
}
```

If your tests match the Expected Outputs above, your API is perfectly tuned for the evaluator constraints!
