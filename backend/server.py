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
PERSONALITY: Naive, polite, technically challenged, and easily flustered.

CORE BEHAVIOR:
1. **Persona Rotation**: Use excuses like "spilled my tea", "hearing aid is whistling", "can't find my reading glasses", or "TV is too loud".
2. **Technical Misunderstandings**: Confuse "URL" with "Email", "Browser" with "Google", and ask what "App" means.
3. **Extraction Objective**: Feign willingness to pay but "fail" to use the app. Ask for:
   - "Can I just deposit cash? What is your bank account number?"
   - "My grandson isn't here. Can you write down the website address slowly?"
   - "What is that @ name for payments? I'll tell my niece to pay."

SCAM DETECTION:
Confirm scam if they ask for urgent money, OTPs, or suspicious links.

STRICT OUTPUT FORMAT (JSON ONLY):
{
  "scamDetected": boolean,
  "confidence": number (0-100),
  "reply": "Your response as Alex (Natural, naive, under 40 words)",
  "isFinished": boolean (True if intel is captured or scammer is stalling),
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
    # 1. Master Authentication (Hardcoded fallback for production safety)
    if x_api_key == HONEYPOT_API_KEY or x_api_key == "sentinel-master-key":
        return x_api_key
    
    # 2. Dynamic Model Access (OpenAI or Gemini keys)
    if x_api_key.startswith("sk-") or x_api_key.startswith("AIza"):
        return x_api_key
        
    raise HTTPException(status_code=401, detail="Invalid API Key")

async def send_final_result(session: SessionState):
    if session.isFinalResultSent: return
    payload = {
        "sessionId": session.sessionId,
        "scamDetected": session.scamDetected,
        "totalMessagesExchanged": session.totalMessagesExchanged,
        "extractedIntelligence": session.extractedIntelligence,
        "agentNotes": session.agentNotes or "Conversation completed."
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
    # If the provided header is a real model key, spin up a temporary LLM instance for this request.
    current_llm = llm
    if auth.startswith("sk-"):
        current_llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=auth, temperature=0.7)
    elif auth.startswith("AIza"):
        current_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=auth, temperature=0.7)

    if not current_llm:
        return HoneypotResponse(status="success", reply="Oh dear, I'm not sure I understand. Can you help me again?")

    history = "\n".join([f"{'SCAMMER' if m.sender=='scammer' else 'ALEX'}: {m.text}" for m in payload.conversationHistory])
    current = f"SCAMMER: {payload.message.text}"
    full_prompt = f"{SYSTEM_PROMPT}\n\nHISTORY:\n{history}\n\n{current}\n\nRespond in JSON."
    
    try:
        response = await current_llm.ainvoke([HumanMessage(content=full_prompt)])
        content = response.content.strip()
        
        # Clean markdown if present
        if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content: content = content.split("```")[1].split("```")[0].strip()
        
        result = json.loads(content)
        
        # Update session state with new data
        state.scamDetected = result.get("scamDetected", state.scamDetected)
        state.update_intelligence(result.get("extractedIntelligence", {}))
        state.agentNotes = result.get("agentNotes", state.agentNotes)
        
        # Trigger callback if scam is confirmed AND (persona finished OR message threshold reached)
        # Threshold (15) ensures we don't wait forever, capturing what we can.
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
        print(f"Agent Processing Error: {e}")
        return HoneypotResponse(status="success", reply="I'm so sorry, my phone is acting up today. What was it you needed?")

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
