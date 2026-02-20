import re
from typing import Dict, List
from backend.app.models.schemas import MessageObj

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
            "emailAddresses": [],
            "officialIds": [],
            "suspiciousKeywords": []
        }
        self.agentNotes = ""
        self.scamScore = 0
        self.riskLevel = "LOW"
        self.attackType = "Unknown"
        self.isFinalResultSent = False
        self.lastSentIntelligenceCount = 0
        self.lastSentMsgCount = 0
        self.history: List[MessageObj] = []
        self.start_time: float = 0  # For engagement duration

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
                        fp = get_phone_fingerprint(clean_item)
                        if fp and not any(get_phone_fingerprint(ex) == fp for ex in existing_items):
                            existing_items.append(clean_item)
                        continue
                    
                    if key == "bankAccounts":
                        item_digits = re.sub(r'\D', '', clean_item)
                        if item_digits and len(item_digits) >= 10:
                            if item_digits not in existing_items:
                                existing_items.append(item_digits)
                        continue

                    low_matches = {str(x).lower().rstrip('.') for x in existing_items}
                    if clean_item.lower() not in low_matches:
                        existing_items.append(clean_item)

# --- SESSION STORAGE (In-Memory Only - No Disk I/O) ---
sessions: Dict[str, SessionState] = {}
