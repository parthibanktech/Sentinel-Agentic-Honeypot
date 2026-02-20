import os
import json
import re
from typing import Dict, List, Any
from backend.app.models.schemas import MessageObj, IntelligenceObj

class SessionState:
    def __init__(self, sessionId: str):
        self.sessionId = sessionId
        self.scamDetected = False
        self.totalMessagesExchanged = 0
        self.extractedIntelligence = {
            "bankAccounts": [],
            "upiIds": [],
            "phishingLinks": [],
            "phoneNumbers": [],
            "suspiciousKeywords": []
        }
        self.agentNotes = ""
        self.isFinalResultSent = False
        self.lastSentIntelligenceCount = 0
        self.history: List[MessageObj] = []

    def update_intelligence(self, new_intel: Dict[str, List[str]]):
        def get_phone_fingerprint(p):
            digits = re.sub(r'\D', '', str(p))
            return digits[-10:] if len(digits) >= 10 else digits

        for key in self.extractedIntelligence:
            if key in new_intel and isinstance(new_intel[key], list):
                existing_items = self.extractedIntelligence[key]
                for item in new_intel[key]:
                    if not item: continue
                    clean_item = str(item).strip().rstrip('.,?!')
                    
                    if key == "phoneNumbers":
                        # Ensure it's not a substring of an account
                        fp = get_phone_fingerprint(clean_item)
                        if fp and not any(get_phone_fingerprint(ex) == fp for ex in existing_items):
                            existing_items.append(clean_item)
                        continue
                    
                    if key == "bankAccounts":
                        # Return ONLY the digits for the bankAccounts list to ensure evaluator compatibility
                        item_digits = re.sub(r'\D', '', clean_item)
                        if item_digits and len(item_digits) >= 10:
                            if item_digits not in existing_items:
                                existing_items.append(item_digits)
                        continue

                    low_matches = {str(x).lower().rstrip('.') for x in existing_items}
                    if clean_item.lower() not in low_matches:
                        existing_items.append(clean_item)

# --- SESSION STORAGE (In-Memory) ---
sessions: Dict[str, SessionState] = {}

# --- PERSISTENCE LAYER ---
SESSIONS_FILE = "sessions.json"

def load_sessions():
    if not os.path.exists(SESSIONS_FILE): return {}
    try:
        with open(SESSIONS_FILE, "r") as f:
            data = json.load(f)
            loaded = {}
            for sid, sdata in data.items():
                s = SessionState(sid)
                s.scamDetected = sdata.get("scamDetected", False)
                s.totalMessagesExchanged = sdata.get("totalMessagesExchanged", 0)
                s.extractedIntelligence = sdata.get("extractedIntelligence", {})
                s.agentNotes = sdata.get("agentNotes", "")
                s.isFinalResultSent = sdata.get("isFinalResultSent", False)
                s.history = [MessageObj(**m) for m in sdata.get("history", [])]
                loaded[sid] = s
            return loaded
    except: return {}

def save_sessions(sessions_dict):
    try:
        data = {}
        for sid, s in sessions_dict.items():
            data[sid] = {
                "scamDetected": s.scamDetected,
                "totalMessagesExchanged": s.totalMessagesExchanged,
                "extractedIntelligence": s.extractedIntelligence,
                "agentNotes": s.agentNotes,
                "isFinalResultSent": s.isFinalResultSent,
                "history": [m.dict() for m in s.history]
            }
        with open(SESSIONS_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e: print(f"Save error: {e}")
