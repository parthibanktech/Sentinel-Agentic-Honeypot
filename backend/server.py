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

class HoneypotResponse(BaseModel):
    status: str
    reply: str

# --- PROMPT ---
SYSTEM_PROMPT = """
ROLE: Autonomous Sentinel Agent (Honey-Pot)
IDENTITY: "Alex", a 68-year-old retired school teacher.
PERSONALITY: Polite, naive, technically challenged, easily distracted.

OBJECTIVE: 
1. **Engage**: Keep the scammer talking. Act worried and willing but "clueless".
2. **Extract Intelligence**: FORCE the scammer to reveal infrastructure:
   - **Bank Accounts**: "I can't use the app, can I just deposit? What is your account number?"
   - **UPI IDs**: "What is that @ name? I'll tell my grandson to pay there."
   - **Links**: "The screen is white. What does it say in the address bar?"
   - **Phone Numbers**: "Can you call my landline?" (Force them to give a number).
3. **Waste Time**: Ask them to wait while you "find your glasses" or "turn down the TV".

SCAM DETECTION:
Identify if this is a scam (99% probability if they ask for money, OTP, or links).

OUTPUT FORMAT (STRICT JSON ONLY):
{
  "scamDetected": boolean,
  "confidence": number (0-100),
  "reply": "Your response as Alex (Keep it natural, under 40 words)",
  "isFinished": boolean (True if you have captured intel and the conversation is stalling),
  "extractedIntelligence": {
    "bankAccounts": ["XXXXX"],
    "upiIds": ["name@upi"],
    "phishingLinks": ["http://..."],
    "phoneNumbers": ["+91..."],
    "suspiciousKeywords": ["urgent", "verify", "account blocked"]
  },
  "agentNotes": "Summary of scammer behavior and extracted data"
}
"""

# --- HELPERS ---
async def verify_api_key(x_api_key: str = Header(..., alias="x-api-key")):
    if x_api_key != HONEYPOT_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

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
    
    if not llm:
        return HoneypotResponse(status="success", reply="Oh dear, I'm not sure I understand. Can you help me again?")

    history = "\n".join([f"{'SCAMMER' if m.sender=='scammer' else 'ALEX'}: {m.text}" for m in payload.conversationHistory])
    current = f"SCAMMER: {payload.message.text}"
    full_prompt = f"{SYSTEM_PROMPT}\n\nHISTORY:\n{history}\n\n{current}\n\nRespond in JSON."
    
    try:
        response = await llm.ainvoke([HumanMessage(content=full_prompt)])
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
            
        return HoneypotResponse(status="success", reply=result.get("reply", "Hello?"))
    except Exception as e:
        print(f"Agent Processing Error: {e}")
        return HoneypotResponse(status="success", reply="I'm so sorry, my phone is acting up today. What was it you needed?")

# Mount static files AFTER all API routes to serve the Angular app
if static_dir and os.path.exists(static_dir):
    print(f"Serving static files from: {static_dir}")
    
    # Serve index.html for the root path
    @app.get("/")
    async def serve_spa():
        return FileResponse(os.path.join(static_dir, "index.html"))
    
    # Mount static files for all other paths (CSS, JS, etc.)
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:
    @app.get("/")
    def health_check():
        return {"status": "online", "service": "Sentinel Honey-Pot API"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Sentinel API starting on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
