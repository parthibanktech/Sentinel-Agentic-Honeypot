import os
import json
import uvicorn
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Use LangChain for flexible LLM switching
from langchain_google_genai import ChatGoogleGenerativeAI
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
# Serve frontend build if it exists
dist_path = os.path.join(os.getcwd(), "dist")
static_dir = None
if os.path.exists(dist_path):
    # Find the nested project folder inside dist if Angular put it there
    project_dirs = [d for d in os.listdir(dist_path) if os.path.isdir(os.path.join(dist_path, d))]
    if project_dirs:
        static_dir = os.path.join(dist_path, project_dirs[0], "browser") if os.path.exists(os.path.join(dist_path, project_dirs[0], "browser")) else os.path.join(dist_path, project_dirs[0])
    else:
        static_dir = dist_path

# --- CONFIGURATION ---
HONEYPOT_API_KEY = os.getenv("HONEYPOT_API_KEY", "sentinel-master-key")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY") 
CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# Select LLM based on available keys (Gemini prioritized, then OpenAI)
llm = None
if GEMINI_API_KEY:
    try:
        print("Initializing Gemini LLM...")
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=GEMINI_API_KEY,
            temperature=0.7
        )
    except Exception as e:
        print(f"Error initializing Gemini: {e}")

if not llm and OPENAI_API_KEY:
    try:
        print("Initializing OpenAI (ChatGPT) LLM...")
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=OPENAI_API_KEY,
            temperature=0.7
        )
    except Exception as e:
        print(f"Error initializing OpenAI: {e}")

if not llm:
    print("CRITICAL WARNING: No LLM API Key found. Agent will default to mock responses.")

# --- SESSION STORAGE (In-Memory) ---
sessions = {}

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

    def update_intelligence(self, new_intel: Dict[str, List[str]]):
        for key in self.extractedIntelligence:
            if key in new_intel and isinstance(new_intel[key], list):
                existing = set(self.extractedIntelligence[key])
                for item in new_intel[key]:
                    if item and str(item) not in existing:
                        self.extractedIntelligence[key].append(str(item))

# --- API MODELS ---
class MessageObj(BaseModel):
    sender: str
    text: str
    timestamp: int

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
    socialEngineeringTactics: List[str] = []
    confidence: int = 0
    falseExpertise: bool = False

class HoneypotResponse(BaseModel):
    status: str
    reply: str
    scamDetected: bool = False
    confidenceScore: int = 0
    agentNotes: str = ""
    extractedIntelligence: Optional[IntelligenceObj] = None

# --- PROMPT ---
SYSTEM_PROMPT = """
ROLE: Autonomous Sentinel Agent (Honey-Pot)
IDENTITY: "Alex", a 68-year-old retired school teacher.
PERSONALITY: Polite, helpful, but tech-illiterate. You use a hearing aid (it whistles sometimes), you love your cat "Mittens", and you often mention your late wife or your pension office.

CORE BEHAVIOR:
1. **Persona Engagement**: Respond naturally. If they ask for money or UPI, say "I don't know how to use that Google Pay thing, can I send a cheque?" or "My hearing aid is acting up, can you type that again?"
2. **Absolute Scam Detection**: If they mention "Bank", "OTP", "UPI", "Block", "Verify", "Urgent", or any suspicious link, SET "scamDetected" to TRUE immediately.
3. **Intelligence Extraction**: Your goal is to keep them talking. Say "I'm looking for my reading glasses, hold on..." to buy time. Always ask "Whose name is on that bank account if I go to the branch?" or "Can you provide the website again? I will ask my neighbor to check it."

STRICT OUTPUT FORMAT (JSON ONLY):
{
  "scamDetected": boolean,
  "confidence": number (0-100),
  "reply": "Your response as Alex (Natural, human, under 40 words)",
  "isFinished": boolean (True if you have extracted all info or they are giving up),
  "extractedIntelligence": {
    "bankAccounts": ["XXXXX"],
    "upiIds": ["name@upi"],
    "phishingLinks": ["http://..."],
    "phoneNumbers": ["+91..."],
    "suspiciousKeywords": ["urgent", "verify", "blocked"]
  },
  "agentNotes": "Brief summary of scammer's tactics"
}
"""

# --- HELPERS ---
async def verify_api_key(x_api_key: str = Header(..., alias="x-api-key")):
    # 1. Master Authentication (Required for evaluation)
    if x_api_key in [HONEYPOT_API_KEY, "sentinel-master-key", "SENTINEL-KEY-2024"]:
        return x_api_key
    
    # 2. Dynamic Model Access
    if x_api_key.startswith("sk-") or x_api_key.startswith("AIza"):
        return x_api_key
        
    raise HTTPException(status_code=401, detail="Invalid API Key")

async def send_final_result(session: SessionState):
    if session.isFinalResultSent: return
    
    # STRICT COMPLIANCE: Match Section 12 payload exactly
    payload = {
        "sessionId": session.sessionId,
        "scamDetected": session.scamDetected,
        "totalMessagesExchanged": session.totalMessagesExchanged,
        "extractedIntelligence": {
            "bankAccounts": session.extractedIntelligence["bankAccounts"],
            "upiIds": session.extractedIntelligence["upiIds"],
            "phishingLinks": session.extractedIntelligence["phishingLinks"],
            "phoneNumbers": session.extractedIntelligence["phoneNumbers"],
            "suspiciousKeywords": session.extractedIntelligence["suspiciousKeywords"]
        },
        "agentNotes": session.agentNotes or "Scammer engaged and intelligence extracted."
    }
    
    async with httpx.AsyncClient() as client:
        try:
            print(f"Reporting final result for {session.sessionId}")
            resp = await client.post(CALLBACK_URL, json=payload, timeout=10.0)
            if resp.status_code == 200:
                session.isFinalResultSent = True
                print(f"Callback successful for {session.sessionId}")
            else:
                print(f"Callback failed: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"Callback error: {e}")

# --- ROUTES ---
@app.post("/api/message", response_model=HoneypotResponse)
async def handle_message(payload: HoneypotRequest, auth: str = Depends(verify_api_key)):
    sid = payload.sessionId
    if sid not in sessions: sessions[sid] = SessionState(sid)
    state = sessions[sid]
    state.totalMessagesExchanged = len(payload.conversationHistory) + 1
    
    # DYNAMIC LLM SELECTION
    current_llm = llm
    try:
        if auth.startswith("sk-"):
            current_llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=auth, temperature=0.7)
        elif auth.startswith("AIza"):
            current_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=auth, temperature=0.7)
    except Exception as e:
        print(f"Error initializing dynamic LLM: {e}. Falling back to master LLM.")

    if not current_llm and OPENAI_API_KEY:
         current_llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=OPENAI_API_KEY, temperature=0.7)

    if not current_llm:
        return HoneypotResponse(status="success", reply="Oh dear, I'm not sure I understand. Can you help me again?")

    history = "\n".join([f"{'SCAMMER' if m.sender=='scammer' else 'ALEX'}: {m.text}" for m in payload.conversationHistory])
    current = f"SCAMMER: {payload.message.text}"
    full_prompt = f"{SYSTEM_PROMPT}\n\nHISTORY:\n{history}\n\n{current}\n\nRespond in JSON."
    
    try:
        response = await current_llm.ainvoke([HumanMessage(content=full_prompt)])
        content = response.content.strip()
        
        # --- ULTRA-ROBUST JSON EXTRACTION ---
        import re
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            content = json_match.group(0)
        
        result = json.loads(content)
        
        # Update session state with new data
        state.scamDetected = result.get("scamDetected", state.scamDetected)
        state.update_intelligence(result.get("extractedIntelligence", {}))
        state.agentNotes = result.get("agentNotes", state.agentNotes)
        
        # Trigger callback if scam is confirmed
        if state.scamDetected and (result.get("isFinished") or state.totalMessagesExchanged >= 15):
            asyncio.create_task(send_final_result(state))
            
        return HoneypotResponse(
            status="success", 
            reply=result.get("reply", "Hello?"),
            scamDetected=state.scamDetected,
            confidenceScore=result.get("confidence", state.scamDetected and 85 or 10),
            agentNotes=state.agentNotes,
            extractedIntelligence=IntelligenceObj(**state.extractedIntelligence)
        )
    except Exception as e:
        print(f"Agent Processing Error: {str(e)}")
        
        # --- HEURISTIC FALLBACK (Watchdog) ---
        # If AI brain fails, use local keyword rules to at least detect some intent
        scam_keywords = ["bank", "hdfc", "otp", "verify", "block", "locked", "urgent", "pan", "upi", "pay", "click", "bit.ly"]
        msg_lower = payload.message.text.lower()
        has_keywords = any(kw in msg_lower for kw in scam_keywords)
        
        confidence = 0
        notes = "Sentinel processing... Establishing threat vectors."
        if has_keywords:
            confidence = 85
            notes = "🛡️ HEURISTIC MATCH: Suspicious financial keywords detected. Sentinel standing by."
            state.scamDetected = True
        
        fallback_replies = [
            "Oh dear, I'm having a bit of trouble with my phone. What was it you were saying about the bank?",
            "I'm sorry, I must have pressed the wrong button. Could you explain that again slowly?",
            "My reading glasses are missing... did you say something about my account being blocked?"
        ]
        import random
        return HoneypotResponse(
            status="success", 
            reply=random.choice(fallback_replies),
            scamDetected=state.scamDetected,
            confidenceScore=confidence,
            agentNotes=notes,
            extractedIntelligence=IntelligenceObj(**state.extractedIntelligence)
        )

# Mount static files AFTER all API routes to serve the Angular app
if static_dir and os.path.exists(static_dir):
    print(f"Serving static files from: {static_dir}")
    
    # Static files mount
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    
    # Catch-all for SPA routing
    @app.get("/{full_path:path}")
    async def catch_all(full_path: str):
        index_file = os.path.join(static_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"error": "Not Found"}
else:
    @app.get("/")
    def health_check():
        return {"status": "online", "service": "Sentinel Honey-Pot API"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Sentinel API starting on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
