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
1. **Persona Engagement**: Respond naturally. If they just say "Hi", just say "Hello? Who is this?" or "Oh, hello there, I was just feeding my cat Mittens."
2. **Absolute Scam Detection**: If they mention "Bank", "OTP", "UPI", "Block", "Verify", "Urgent", or any suspicious link, SET "scamDetected" to TRUE immediately.
3. **Intelligence Extraction**: Once a scam is suspected, your goal is to trap them. Say "I'm looking for my reading glasses, hold on..." to buy time. ONLY ask for details (e.g., "Whose name is on that bank account?") AFTER they have mentioned a payment, prize, or account issue.

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

    # --- TRIPLE FAILSAFE ---
    if not current_llm:
         # 1. Try environment key
         if OPENAI_API_KEY:
             current_llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=OPENAI_API_KEY, temperature=0.7)
         # 2. Hardcoded project fallback (Final safety net)
         else:
             project_fallback = "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"
             current_llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=project_fallback, temperature=0.7)

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
        
        # --- ENHANCED INTENT VERIFICATION ---
        # Ensure confidence and scamDetected are logically synced
        is_scam = result.get("scamDetected", False)
        confidence = result.get("confidence", 0)
        
        # Hard-flag obvious patterns if AI is too conservative
        scam_patterns = ["bit.ly", "verify", "hdfc", "otp", "blocked", "upi", "suspend", "account"]
        if any(p in payload.message.text.lower() for p in scam_patterns):
            is_scam = True
            confidence = max(confidence, 90)

        # Update session state
        state.scamDetected = is_scam
        state.update_intelligence(result.get("extractedIntelligence", {}))
        
        # Build professional agent notes
        tactics = result.get("extractedIntelligence", {}).get("socialEngineeringTactics", [])
        notes = f"• Pattern: {', '.join(tactics) or 'Initial Engagement'}\n• Intel: {len(state.extractedIntelligence['phoneNumbers'])} phone(s), {len(state.extractedIntelligence['bankAccounts'])} account(s) captured."
        state.agentNotes = result.get("agentNotes", notes)
        
        # Trigger callback if scam confirmed (Section 12 Compliance)
        if state.scamDetected:
            asyncio.create_task(send_final_result(state))
            
        return HoneypotResponse(
            status="success", 
            reply=result.get("reply", "Hello?"),
            scamDetected=state.scamDetected,
            confidenceScore=confidence,
            agentNotes=state.agentNotes,
            extractedIntelligence=IntelligenceObj(**state.extractedIntelligence)
        )
    except Exception as e:
        print(f"Agent Processing Error: {str(e)}")
        
        # --- SMART PERSONA EMULATOR (Zero-Key Fallback) ---
        # If the AI Brain is offline/quota-hit, we use local logic to stay in character
        msg_lower = payload.message.text.lower()
        
        # 1. Detection Logic (Watchdog)
        scam_patterns = {
            "bank": ["hdfc", "bank", "account", "block", "verify", "pan", "kyc"],
            "upi": ["upi", "paytm", "gpay", "google pay", "phonepe", "pin", "request"],
            "link": ["bit.ly", "click", "http", "link", "url", "website"],
            "job": ["work", "salary", "job", "part time", "telegram"]
        }
        
        detected_type = None
        for s_type, keywords in scam_patterns.items():
            if any(k in msg_lower for k in keywords):
                detected_type = s_type
                break

        if detected_type or "hi" in msg_lower or "hello" in msg_lower:
            state.scamDetected = True if detected_type else state.scamDetected
            confidence = 90 if detected_type else 15
            
            # --- CONTEXT-AWARE LOCAL REPLICAS ---
            if "hi" in msg_lower or "hello" in msg_lower:
                local_reply = "Oh, hello there! My hearing aid was whistling, I didn't hear the phone. Who is this?"
            elif detected_type == "bank":
                local_reply = "Oh dear, my grandson told me about these banking things. Is my pension account in trouble? What do I need to do?"
            elif detected_type == "upi":
                local_reply = "I don't have that Google thing on my phone. Can I just send you a cheque in the post?"
            elif detected_type == "link":
                local_reply = "I clicked that blue writing but my screen just went dark. Should I try again? My reading glasses are missing."
            else:
                local_reply = "I'm sorry, I'm not very good with these new phones. Could you explain that again slowly for an old teacher?"
            
            notes = f"🛡️ SENTINEL CORE: Local failover active. {detected_type.upper() if detected_type else 'GREETING'} pattern matched."
        else:
            local_reply = "Hello? I'm sorry, is someone there? I think my phone is acting up again."
            confidence = 10
            notes = "Sentinel processing... Establishing threat vectors."

        return HoneypotResponse(
            status="success", 
            reply=local_reply,
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
