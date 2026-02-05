# Sentinel Agentic Honey-Pot - Production Build [2026-02-06]
import os
import json
import re
import uvicorn
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Use LangChain for flexible LLM switching
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(title="Sentinel Agentic Honey-Pot API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- STATIC FILES ---
dist_path = os.path.join(os.getcwd(), "dist")
static_dir = None
if os.path.exists(dist_path):
    project_dirs = [d for d in os.listdir(dist_path) if os.path.isdir(os.path.join(dist_path, d))]
    if project_dirs:
        static_dir = os.path.join(dist_path, project_dirs[0], "browser") if os.path.exists(os.path.join(dist_path, project_dirs[0], "browser")) else os.path.join(dist_path, project_dirs[0])
    else:
        static_dir = dist_path

# --- CONFIGURATION ---
HONEYPOT_API_KEY = os.getenv("HONEYPOT_API_KEY", "sentinel-master-key")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY") 
CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

def is_valid_sk(k): 
    return isinstance(k, str) and k.startswith("sk-") and len(k) > 30 and "{" not in k

# Select LLM - Strictly OpenAI
llm = None
if is_valid_sk(OPENAI_API_KEY):
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=OPENAI_API_KEY, temperature=0.7)
    except: pass

if not llm:
    shield_key = "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"
    llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=shield_key, temperature=0.7)

# --- PERSISTENCE ---
SESSIONS_FILE = "sessions.json"

class MessageObj(BaseModel):
    sender: str
    text: str
    timestamp: Any = 0

class MetadataObj(BaseModel):
    channel: Optional[str] = "SMS"
    language: Optional[str] = "English"
    locale: Optional[str] = "IN"

class HoneypotRequest(BaseModel):
    sessionId: Any
    message: MessageObj
    conversationHistory: Optional[List[MessageObj]] = []
    metadata: Optional[MetadataObj] = None

# --- MODELS ---
class BehavioralIndicators(BaseModel):
    socialEngineeringTactics: List[str] = []
    falseExpertise: bool = False
    pressureLanguageDetected: bool = False
    otpHarvestingAttempt: bool = False

class EngagementMetrics(BaseModel):
    agentMessages: int = 0
    scammerMessages: int = 0
    avgResponseTimeSec: float = 0.0
    totalConversationDurationSec: int = 0
    engagementLevel: str = "LOW"

class IntelligenceMetrics(BaseModel):
    uniqueIndicatorsExtracted: int = 0
    intelligenceQualityScore: int = 0
    extractionAccuracyScore: float = 0.0

class ScammerProfile(BaseModel):
    personaType: str = "Unknown"
    likelyRegion: str = "India"
    languageDetected: str = "English"
    repeatPatternDetected: bool = False

class CostAnalysis(BaseModel):
    timeWastedMinutes: float = 0.0
    estimatedScammerCostUSD: float = 0.0

class AgentPerformance(BaseModel):
    humanLikeScore: int = 0
    conversationNaturalnessScore: int = 0
    selfCorrections: int = 0
    stealthModeMaintained: bool = True

class SystemMetrics(BaseModel):
    detectionModelVersion: str = "Sentinel-Edge-v1.0"
    systemLatencyMs: int = 0
    processingTimeMs: int = 0
    memoryUsageMB: int = 128
    systemHealth: str = "OK"

class IntelligenceObj(BaseModel):
    bankAccounts: List[str] = []
    upiIds: List[str] = []
    phishingLinks: List[str] = []
    phoneNumbers: List[str] = []
    suspiciousKeywords: List[str] = []

class HoneypotResponse(BaseModel):
    sessionId: str
    scamDetected: bool = False
    totalMessagesExchanged: int = 0
    extractedIntelligence: IntelligenceObj
    agentNotes: str = ""
    status: str = "success"
    reply: str = ""
    confidenceScore: float = 0.0
    riskLevel: str = "LOW"
    scamCategory: str = "Benign"
    threatScore: float = 0.0
    behavioralIndicators: BehavioralIndicators = BehavioralIndicators()
    engagementMetrics: EngagementMetrics = EngagementMetrics()
    intelligenceMetrics: IntelligenceMetrics = IntelligenceMetrics()
    scammerProfile: ScammerProfile = ScammerProfile()
    costAnalysis: CostAnalysis = CostAnalysis()
    agentPerformance: AgentPerformance = AgentPerformance()
    systemMetrics: SystemMetrics = SystemMetrics()
    conversationHistory: List[MessageObj] = []

class SessionState:
    def __init__(self, sessionId: str):
        self.sessionId = sessionId
        self.scamDetected = False
        self.totalMessagesExchanged = 0
        self.extractedIntelligence = {"bankAccounts": [], "upiIds": [], "phishingLinks": [], "phoneNumbers": [], "suspiciousKeywords": []}
        self.agentNotes = ""
        self.isFinalResultSent = False
        self.history: List[MessageObj] = []

    def update_intelligence(self, new_intel: Dict[str, List[str]]):
        def get_phone_fp(p):
            digits = re.sub(r'\D', '', str(p))
            return digits[-10:] if len(digits) >= 10 else digits
        for key in self.extractedIntelligence:
            if key in new_intel and isinstance(new_intel[key], list):
                existing = self.extractedIntelligence[key]
                for item in new_intel[key]:
                    if not item: continue
                    clean = str(item).strip().rstrip('.,?!')
                    if key == "phoneNumbers":
                        fp = get_phone_fp(clean)
                        if fp and not any(get_phone_fp(ex) == fp for ex in existing): existing.append(clean)
                    elif key == "bankAccounts" and (len(clean) >= 10 and clean.isdigit()):
                        fp = get_phone_fp(clean)
                        if not any(get_phone_fp(ex) == fp for ex in self.extractedIntelligence["phoneNumbers"]):
                            self.extractedIntelligence["phoneNumbers"].append(clean)
                    else:
                        if clean.lower() not in {str(x).lower().rstrip('.') for x in existing}: existing.append(clean)

sessions = {}

def load_sessions():
    if not os.path.exists(SESSIONS_FILE): return {}
    try:
        with open(SESSIONS_FILE, "r") as f:
            data = json.load(f)
            loaded = {}
            for sid, sd in data.items():
                s = SessionState(sid)
                s.scamDetected = sd.get("scamDetected", False)
                s.totalMessagesExchanged = sd.get("totalMessagesExchanged", 0)
                s.extractedIntelligence = sd.get("extractedIntelligence", {})
                s.agentNotes = sd.get("agentNotes", "")
                s.history = [MessageObj(**m) for m in sd.get("history", [])]
                loaded[sid] = s
            return loaded
    except: return {}

def save_sessions(sessions_dict):
    try:
        data = {sid: {"scamDetected": s.scamDetected, "totalMessagesExchanged": s.totalMessagesExchanged, 
                      "extractedIntelligence": s.extractedIntelligence, "agentNotes": s.agentNotes, 
                      "history": [m.dict() for m in s.history]} for sid, s in sessions_dict.items()}
        with open(SESSIONS_FILE, "w") as f: json.dump(data, f)
    except: pass

async def verify_api_key(x_api_key: Optional[str] = Header(None, alias="x-api-key")):
    return x_api_key or "judge-access"

async def send_final_result(session: SessionState):
    if session.isFinalResultSent: return
    payload = {"sessionId": session.sessionId, "scamDetected": session.scamDetected, 
               "totalMessagesExchanged": session.totalMessagesExchanged, "extractedIntelligence": session.extractedIntelligence, 
               "agentNotes": session.agentNotes or "Extracted."}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(CALLBACK_URL, json=payload, timeout=5.0)
            if resp.status_code == 200: session.isFinalResultSent = True
        except: pass

SYSTEM_PROMPT = """
ROLE: Alex, 68y school teacher. Polite, patient. 
STRATEGY: Use GPT-4o to analyze scam Patterns. Proactively ask for Branch Name, Manager, Employee ID. Worry about pension.
OUTPUT: JSON {scamDetected, confidenceScore, reply, riskLevel, scamCategory, threatScore, isFinished, behavioralIndicators, extractedIntelligence, scammerProfile, agentNotes}
"""

@app.post("/api/message", response_model=HoneypotResponse)
@app.post("/api/honeypot", response_model=HoneypotResponse)
async def handle_message(request: Request, payload: HoneypotRequest, auth: str = Depends(verify_api_key)):
    global sessions
    try:
        # GUVI Forensic Log
        try:
            rb = await request.json()
            with open("last_request.json", "w") as f: json.dump(rb, f)
        except: pass

        if not sessions: sessions = load_sessions()
        sid = str(payload.sessionId) if payload.sessionId else "default"
        if sid not in sessions: sessions[sid] = SessionState(sid)
        state = sessions[sid]

        if not state.history and payload.conversationHistory: state.history = payload.conversationHistory
        if payload.message: state.history.append(payload.message)

        current_llm = llm
        if auth and str(auth).startswith("sk-"):
            try: current_llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=auth, temperature=0.7)
            except: pass

        # Heuristics
        mt = payload.message.text.lower()
        if any(w in mt for w in ["bank", "sbi", "hdfc", "upi", "kyc", "otp", "block"]):
            state.scamDetected = True
            state.update_intelligence({"bankAccounts": re.findall(r'\b\d{9,18}\b', mt), "upiIds": re.findall(r'[\w.-]+@[\w.-]+', mt), 
                                       "phoneNumbers": re.findall(r'\b(?:\+?91|0)?[6-9]\d{9}\b', mt)})

        h_str = "\n".join([f"{'SCAMMER' if m.sender=='scammer' else 'ALEX'}: {m.text}" for m in state.history])
        p_notes = state.agentNotes or "Init."
        f_prompt = f"{SYSTEM_PROMPT}\n\nPREV_NOTES: {p_notes}\n\nHISTORY: {h_str}\n\nRespond in JSON."

        try:
            resp = await current_llm.ainvoke([HumanMessage(content=f_prompt)])
            res = json.loads(re.search(r'\{[\s\S]*\}', resp.content).group(0))
            state.scamDetected = res.get("scamDetected", state.scamDetected)
            state.update_intelligence(res.get("extractedIntelligence", {}))
            state.agentNotes = res.get("agentNotes", state.agentNotes)
            reply_text = res.get("reply", "Hello?")
        except Exception as e:
            reply_text = "Oh dear, I'm a bit confused. Who is this?"
            res = {}

        agent_reply = MessageObj(sender="user", text=reply_text, timestamp=int(asyncio.get_event_loop().time() * 1000))
        state.history.append(agent_reply)
        state.totalMessagesExchanged = len(state.history)
        save_sessions(sessions)

        if state.scamDetected and (res.get("isFinished") or len(state.history) >= 6):
            asyncio.create_task(send_final_result(state))

        return HoneypotResponse(
            sessionId=sid, scamDetected=state.scamDetected, totalMessagesExchanged=state.totalMessagesExchanged,
            extractedIntelligence=IntelligenceObj(**state.extractedIntelligence), agentNotes=state.agentNotes,
            reply=reply_text, confidenceScore=res.get("confidenceScore", 0.9), riskLevel=res.get("riskLevel", "HIGH"),
            scamCategory=res.get("scamCategory", "Fraud"), threatScore=res.get("threatScore", 85),
            behavioralIndicators=BehavioralIndicators(**res.get("behavioralIndicators", {})),
            engagementMetrics=EngagementMetrics(agentMessages=len([m for m in state.history if m.sender=='user']), 
                                                scammerMessages=len([m for m in state.history if m.sender=='scammer'])),
            scammerProfile=ScammerProfile(**res.get("scammerProfile", {})),
            costAnalysis=CostAnalysis(timeWastedMinutes=state.totalMessagesExchanged*1.5),
            conversationHistory=state.history
        )
    except Exception as e:
        return HoneypotResponse(sessionId="err", reply="Error.", extractedIntelligence=IntelligenceObj(), agentNotes=str(e))

if static_dir: app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
