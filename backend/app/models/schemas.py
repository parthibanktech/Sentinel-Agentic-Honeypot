from typing import List, Optional, Any, Union
from pydantic import BaseModel, field_validator

class MessageObj(BaseModel):
    sender: str
    text: str
    timestamp: Any = 0  # Accept both epoch int AND ISO string

    @field_validator('timestamp', mode='before')
    @classmethod
    def normalize_timestamp(cls, v):
        if isinstance(v, str):
            # Convert ISO string to epoch ms
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
                return int(dt.timestamp() * 1000)
            except:
                return 0
        return v

class MetadataObj(BaseModel):
    channel: Optional[str] = "SMS"
    language: Optional[str] = "English"
    locale: Optional[str] = "IN"

class HoneypotRequest(BaseModel):
    sessionId: str
    message: MessageObj
    conversationHistory: List[MessageObj] = []
    metadata: Optional[MetadataObj] = None

class IntelligenceObj(BaseModel):
    bankAccounts: List[str] = []
    upiIds: List[str] = []
    phishingLinks: List[str] = []
    phoneNumbers: List[str] = []
    suspiciousKeywords: List[str] = []
    emailAddresses: List[str] = []
    officialIds: List[str] = []

class EngagementMetrics(BaseModel):
    totalMessagesExchanged: int = 0
    engagementDurationSeconds: int = 0

class HoneypotResponse(BaseModel):
    """
    Mandatory schema for Hackathon Evaluation (Response Structure: 20 points).
    """
    status: str = "success"
    reply: str
    scamDetected: bool
    extractedIntelligence: IntelligenceObj
    engagementMetrics: Optional[EngagementMetrics] = None
    agentNotes: Optional[str] = ""
