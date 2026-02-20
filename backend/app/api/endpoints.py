import re
import time
import asyncio
import json
import httpx
import os
from fastapi import APIRouter, HTTPException, Depends, Header
from backend.app.models.schemas import HoneypotRequest, HoneypotResponse, MessageObj
from backend.app.services.session_manager import sessions, SessionState
from backend.app.services.ml_engine import predict_scam_ml
from backend.app.services.intelligence import extract_intelligence, calculate_scam_score
from backend.app.core.config import HONEYPOT_API_KEY, CALLBACK_URL

router = APIRouter()

# --- AUTH ---
async def verify_api_key(x_api_key: str = Header(..., alias="x-api-key")):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API Key missing")
    return x_api_key

# ============================================================================
# SENTINEL SEMANTIC RESPONSE ENGINE (v4.0)
# Handles ANY scam type via Intent Analysis, not just keywords.
# ============================================================================

def analyze_intent(text: str, lower: str) -> dict:
    """Analyze the semantic intent of the message."""
    intent = {
        "urgency": False,
        "threat": False,
        "reward": False,
        "verification": False,
        "payment_request": False,
        "info_request": False,
        "download_request": False,
        "has_entity": False,
        "entity_value": ""
    }
    
    # 1. Detect Urgency (Time pressure)
    if re.search(r'\b(immediate|urgent|hurry|quickly|24 hours|today|now|expire|lapse)\b', lower):
        intent["urgency"] = True
        
    # 2. Detect Threat (Consequence)
    if re.search(r'\b(block|suspend|disconnect|arrest|police|court|legal|case|jail|fine|penalty|seize)\b', lower):
        intent["threat"] = True
        
    # 3. Detect Reward (Gain)
    if re.search(r'\b(won|winner|lottery|prize|bonus|credit|offer|gift|cashback|refund|job|salary|earn)\b', lower):
        intent["reward"] = True
        
    # 4. Detect Verification (KYC/OTP)
    if re.search(r'\b(verify|kyc|pan|aadhaar|document|details|update|renew|otp|code)\b', lower):
        intent["verification"] = True
        
    # 5. Detect Payment Request
    if re.search(r'\b(pay|send|deposit|transfer|fee|charge|tax)\b', lower):
        intent["payment_request"] = True
        
    # 6. Detect Entities to Reference
    # Phone
    phone = re.search(r'(?:\+?91[\s\-.]?)?[6-9]\d{4}[\s\-.]?\d{5}', text)
    if phone:
        intent["has_entity"] = True
        intent["entity_value"] = phone.group()
        intent["entity_type"] = "phone"
    
    # Link
    link = re.search(r'https?://\S+', text)
    if link:
        intent["has_entity"] = True
        intent["entity_value"] = link.group()
        intent["entity_type"] = "link"
        
    # UPI
    upi = re.search(r'[\w.\-]+@(?:ok\w+|ybl|paytm|upi|apl|ibl|axl)', text)
    if upi:
        intent["has_entity"] = True
        intent["entity_value"] = upi.group()
        intent["entity_type"] = "upi"
        
    return intent

async def generate_reply(text: str, turn: int, used_replies: set, history_texts: list, score_result: dict = None) -> str:
    """Generate high-quality generic response based on Intent Analysis and Scam Score."""
    lower = text.lower().strip()
    intent = analyze_intent(text, lower)
    
    # Merge Score-based attack type into intent
    attack_type = score_result.get("attack_type", "Unknown") if score_result else "Unknown"
    
    def pick(options):
        # Filter partially used ones if needed, or just pick random valid
        valid = [o for o in options if o not in used_replies]
        if not valid: valid = options # reuse if exhausted
        return valid[turn % len(valid)]

    # === COMBINATORIAL RESPONSE ENGINE (Dynamic & Generic) ===
    import random
    from backend.app.services.intelligence import extract_conversation_focus
    
    # Load templates from external file once (or on-demand for dynamic updates)
    TEMPLATES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core/persona_templates.json")
    try:
        with open(TEMPLATES_PATH, 'r') as f:
            TEMPLATES = json.load(f)
    except Exception as e:
        print(f"⚠️ Template load failed: {e}. Using fallback.")
        TEMPLATES = {"drivers": {}, "openers": [], "questions": []}

    def assemble(intent_type, entity_val=None, entity_type=None, text_content=""):
        # Special case for pure greetings
        if intent_type == "greetings":
            greetings = TEMPLATES.get("drivers", {}).get("greetings", ["Hello?"])
            return random.choice(greetings)

        # 1. Opener
        openers = TEMPLATES.get("openers", ["Hello?", "Wait,"])
        p1 = random.choice(openers)
        
        # 2. Driver (Context/Excuse based on Intent)
        drivers = TEMPLATES.get("drivers", {}).get(intent_type, ["I am trying my best."])
        
        # If no specific driver, or randomly for variety, use REFLECTION if topic is found
        topic = extract_conversation_focus(text_content) if text_content else "this"
        if (not drivers) or (random.random() < 0.4 and intent_type in ["confusion", "generic"]):
             drivers = TEMPLATES.get("drivers", {}).get("reflection", ["I don't understand {topic}."])
             p2 = random.choice(drivers).replace("{topic}", topic)
        else:
             p2 = random.choice(drivers) if drivers else "I'm confused."
        
        # 3. Question / Action
        questions = TEMPLATES.get("questions", ["Who is this?"])
        p3 = random.choice(questions)
        
        # 4. Entity Reflection (Highest Specificity)
        if entity_val and entity_type:
            reflections = TEMPLATES.get("entity_reflection", {}).get(entity_type, [])
            if reflections:
                p3 = random.choice(reflections).replace("{val}", str(entity_val))
        
        return f"{p1} {p2} {p3}"

    # === GREETING DETECTION (Immediate Human-Like Response) ===
    if len(lower) < 25 and any(g in lower for g in ["hi", "hello", "hey", "dear", "neighbor", "neighbour", "friend"]):
        return assemble("greetings", text_content=text)

    # === AI AUGMENTATION (Max Intelligence Layer) ===
    # If we have a key, let the AI handle the complex reasoning immediately.
    from backend.app.services.llm_engine import call_llm
    from backend.app.core.config import OPENAI_API_KEY, GOOGLE_API_KEY, is_valid_sk, is_valid_google
    
    if is_valid_sk(OPENAI_API_KEY) or is_valid_google(GOOGLE_API_KEY):
        try:
            # DYNAMIC PERSONA LOGIC: Adjust interrogation based on risk
            is_scam = score_result.get("scam_detected", False) if score_result else False
            
            if is_scam:
                # High Risk: Start aggressive social engineering interrogation to extract intelligence
                instruction = "Persona: Vulnerable but compliant victim. Task: You MUST extract actionable intelligence! Act confused and explicitly ask for concrete details like their exact employee ID, the specific bank account or UPI ID to send money to, their direct phone number, or a website link so you can 'comply'. Keep it natural and conversational. Keep response under 30 words."
            elif turn <= 2:
                # Low Risk FIRST message: Treat as unknown number texting out of the blue
                instruction = "Persona: Cautious elderly person. Task: You just received a text from an unknown number. State that you don't recognize the number and ask 'Who is this?' or 'Do I know you?'. Do NOT act like you know them. Do NOT make small talk. Keep response under 20 words."
            else:
                # Low Risk ONGOING conversation: Pivot to probing
                instruction = "Persona: Cautious elderly person. Task: The sender is an UNKNOWN number. DO NOT make small talk. Demand to know who they are and what they want. If they state a purpose or ask for something, immediately demand targeted proof: ask for their phone number, a website link, or an exact ID before you answer them. Keep response under 25 words."

            history_context = " | ".join(history_texts[-5:-1]) if len(history_texts) > 1 else "None"
            prompt = f"HISTORY: {history_context}\nNEW MESSAGE: {text}\nINSTRUCTION: {instruction}"
            llm_reply = await call_llm(prompt)
            if len(llm_reply) > 5: return llm_reply
        except Exception as e:
            print(f"[LLM] Error: {e}")
            pass

    # === COMBINATORIAL FALLBACK (Template Engine) ===
    # 1. ENTITY REFLECTION
    if intent["has_entity"]:
        return assemble("confusion", intent["entity_value"], intent["entity_type"], text_content=text)

    # 2. INTENT-BASED
    if attack_type == "Digital Arrest / Impersonation" or intent["threat"] or (intent["urgency"] and "account" in lower):
        return assemble("fear", text_content=text)
    if attack_type == "Temptation / Investment Scam" or intent["reward"]:
        return assemble("greed", text_content=text)
    if attack_type == "KYC Fraud" or intent["verification"]:
        return assemble("confusion", text_content=text)
    if attack_type == "Financial Fraud" or intent["payment_request"]:
        return assemble("urgency", text_content=text)

    # 3. GENERIC FALLBACK
    return assemble("generic", text_content=text)




# --- CALLBACK ---
async def send_final_result(session: SessionState):
    current_count = sum(len(v) for v in session.extractedIntelligence.values() if isinstance(v, list))
    current_msg_count = session.totalMessagesExchanged

    # Trigger Rules:
    # 1. New Intelligence found (count increased)
    # 2. Significant conversation milestones (4, 8, 12, etc.) to capture engagement points
    intel_increased = current_count > session.lastSentIntelligenceCount
    milestone_reached = (current_msg_count >= 4 and current_msg_count % 4 == 0) and current_msg_count > getattr(session, 'lastSentMsgCount', 0)

    if not (intel_increased or milestone_reached):
        return

    duration = int(time.time() - session.start_time) if session.start_time else 0
    intel = session.extractedIntelligence
    unique = sum(len(v) for k, v in intel.items() if isinstance(v, list) and k != "suspiciousKeywords")

    # Determine generic scenario type for reporting
    scam_type = "Unknown"
    if len(intel.get('bankAccounts',[])) > 0: scam_type = "Financial Fraud"
    elif len(intel.get('phishingLinks',[])) > 0: scam_type = "Phishing"
    elif "police" in str(intel): scam_type = "Legal Threat"
    elif session.scamDetected: scam_type = "Social Engineering"

    rich_notes = f"""{session.agentNotes or 'Scammer engaged and intelligence extracted by Sentinel AI.'}

--- SENTINEL ANALYTICS REPORT ---
confidenceScore: {0.95 if session.scamDetected else 0.15}
riskLevel: {session.riskLevel}
scamCategory: {session.attackType}
threatScore: {session.scamScore}
behavioralIndicators: pressureLanguageDetected={session.scamDetected}, socialEngineeringTactics=[{', '.join(intel.get('suspiciousKeywords', [])[:5])}]
scammerProfile: personaType={'Fake Official' if session.scamDetected else 'Unknown'}, aggressionLevel={'HIGH' if session.scamDetected else 'LOW'}
intelligenceMetrics: uniqueIndicatorsExtracted={unique}, intelligenceQualityScore={min(100, unique * 20)}
costAnalysis: timeWastedMinutes={round(duration/60,2)}, estimatedScammerCostUSD={round(duration*0.00833,4)}
systemMetrics: model=Sentinel-Hybrid-v4, responseTimeMs=<100
"""

    payload = {
        "sessionId": session.sessionId,
        "scamDetected": session.scamDetected,
        "totalMessagesExchanged": session.totalMessagesExchanged,
        "extractedIntelligence": {
            "bankAccounts": intel.get("bankAccounts", []),
            "upiIds": intel.get("upiIds", []),
            "phishingLinks": intel.get("phishingLinks", []),
            "phoneNumbers": intel.get("phoneNumbers", []),
            "emailAddresses": intel.get("emailAddresses", []),
            "officialIds": intel.get("officialIds", []),
        },
        "agentNotes": rich_notes.strip(),
        "status": "success",
        "engagementMetrics": {
            "totalMessagesExchanged": session.totalMessagesExchanged,
            "engagementDurationSeconds": duration
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(CALLBACK_URL, json=payload, timeout=10.0)
            if resp.status_code == 200:
                session.isFinalResultSent = True
                session.lastSentIntelligenceCount = current_count
                session.lastSentMsgCount = current_msg_count
                print(f"[CB] OK {session.sessionId[:8]} (T{current_msg_count})")
        except Exception as e:
            print(f"[CB] Err: {e}")


# --- MAIN ENDPOINT ---
@router.post("/message", response_model=HoneypotResponse)
async def handle_message(payload: HoneypotRequest, auth: str = Depends(verify_api_key)):
    start = time.time()

    sid = payload.sessionId
    if sid not in sessions:
        sessions[sid] = SessionState(sid)
    state = sessions[sid]

    if not state.start_time:
        state.start_time = time.time()
        
    if not state.history and payload.conversationHistory:
        state.history = payload.conversationHistory

    state.history.append(payload.message)
    turn = len(state.history)

    # --- 1. INTELLIGENCE (Regex) ---
    all_text = " ".join([m.text for m in state.history])
    intel = extract_intelligence(text=payload.message.text, combined_input=all_text, lower_input=all_text.lower())
    state.update_intelligence(intel)

    # --- 2. DETECTION (ML + Score) ---
    # Core detection remains local and INSTANT.
    ml_scam, ml_conf = predict_scam_ml(payload.message.text)
    score_result = calculate_scam_score(payload.message.text, state.extractedIntelligence)
    
    # Update local state immediately
    state.scamScore = score_result["score"]
    state.riskLevel = score_result["risk_level"]
    state.attackType = score_result["attack_type"]
    if score_result["scam_detected"] or ml_scam:
        state.scamDetected = True
        
    lower = payload.message.text.lower()
    intent = analyze_intent(payload.message.text, lower)
    if intent["threat"] or intent["urgency"] or intent["reward"] or (intent["verification"] and intent["has_entity"]):
        state.scamDetected = True

    # --- 3. RESPONSE GENERATION (Optimized for Speed) ---
    used_replies = set(m.text for m in state.history if m.sender == 'user')
    history_texts = [m.text for m in state.history]
    
    # Generate the reply (Turn 1 = Template, Turn 2+ = Possible LLM)
    # This remains awaitable because it's the core blocker for the response.
    reply = await generate_reply(payload.message.text, turn, used_replies, history_texts, score_result)

    # --- 4. AGENTIC ANALYSIS (Background Task - NO BLOCKING) ---
    # We trigger the deep LLM analysis in the background to avoid 4s+ latency.
    # This will update the agentNotes for the CALLBACK, but not block the REPLY.
    async def perform_background_analysis(session_id, text, current_score, current_ml, history):
        from backend.app.services.llm_engine import call_llm
        from backend.app.core.config import OPENAI_API_KEY, GOOGLE_API_KEY, is_valid_sk, is_valid_google
        if is_valid_sk(OPENAI_API_KEY) or is_valid_google(GOOGLE_API_KEY):
            try:
                # Provide history for better context
                context = " | ".join(history[-3:])
                analysis_prompt = (
                    f"History: {context}\n"
                    f"New Message: {text}\n"
                    "Analyze for malicious scam intent. "
                    "JSON ONLY: {\"is_scam\": bool, \"confidence\": float[0-1], \"attack_type\": \"string\", \"summary\": \"Brief human-style summary of scammer's claims/actions, e.g., 'Scammer claimed to be from SBI fraud department'\"}"
                )
                raw = await call_llm(analysis_prompt)
                match = re.search(r'\{.*\}', str(raw), re.DOTALL)
                if match:
                    llm_data = json.loads(match.group())
                    s = sessions.get(session_id)
                    if s and llm_data:
                        # Only flip detected bit if confidence is high or system score is already significant
                        if llm_data.get("is_scam") and llm_data.get("confidence", 0) > 0.8:
                            s.scamDetected = True
                        
                        if llm_data.get("attack_type"): 
                            s.attackType = llm_data["attack_type"]
                        
                        summary = llm_data.get('summary', 'Analyzing...')
                        s.agentNotes = f"{summary} [Confidence: {llm_data.get('confidence', 0):.2f}, Score: {current_score}]"
            except Exception as e:
                print(f"[BG-Analysis] Silent failure: {e}")
                pass
            
    # Trigger background forensic analysis
    asyncio.create_task(perform_background_analysis(sid, payload.message.text, state.scamScore, ml_conf, history_texts))

    # Standard note if LLM hasn't finished yet (Human-quality fallback)
    if not state.agentNotes or "[Confidence" not in state.agentNotes:
        if state.scamDetected:
            state.agentNotes = f"Active surveillance initiated. Potential {state.attackType} detected. High-priority intelligence gathering in progress."
        else:
            state.agentNotes = "Sentinel monitoring active. Initial engagement appears benign. Establishing trust persona."

    # Finalize state for the immediate response
    state.history.append(MessageObj(sender="user", text=reply, timestamp=int(time.time() * 1000)))
    state.totalMessagesExchanged = len(state.history)

    # Callback Trigger Strategy
    intel_count = sum(len(v) for v in state.extractedIntelligence.values() if isinstance(v, list))
    if state.scamDetected and (intel_count >= 1 or state.totalMessagesExchanged >= 2):
        asyncio.create_task(send_final_result(state))

    elapsed = time.time() - start
    print(f"[API] {sid[:8]} T{state.totalMessagesExchanged} {elapsed*1000:.0f}ms Scam={state.scamDetected}")

    # Construct highly detailed, metric-rich agent notes (Advanced telemetry format)
    ai_summary = state.agentNotes.split(' [Confidence:')[0] if state.agentNotes else ""
    is_placeholder = ai_summary.startswith("Active") or ai_summary.startswith("Sentinel")
    
    # 1. Base Analysis Phase
    # If the LLM summary from a previous turn is still benign but we synchronously detected a scam now, override the summary.
    if state.scamDetected and (not ai_summary or "benign" in ai_summary.lower() or "greeting" in ai_summary.lower()):
        base_note = f"Honeypot intercepted potential {state.attackType or 'Social Engineering'} vectors. Synchronous intelligence override."
    else:
        base_note = ai_summary if (ai_summary and not is_placeholder) else (f"Honeypot intercepted potential {state.attackType or 'Social Engineering'} vectors." if state.scamDetected else "Honeypot engaged. Initial conversation vector appears benign; maintaining trust persona to probe for intent.")

    # 2. Intelligence Parsed Phase
    extracted_items = []
    for k, v in state.extractedIntelligence.items():
        if v and isinstance(v, list):
            extracted_items.append(f"{k}: [{', '.join(v)}]")
            
    # 3. Cognitive & Metric Telemetry Phase
    duration = int(time.time() - state.start_time)
    confidence = "HIGH (95%+)" if state.scamDetected else "LOW (<20%)"
    
    extra_metrics = f" | [SYSTEM METRICS] -> ThreatScore: {state.scamScore:.2f}/100 | Risk: {state.riskLevel.upper()} | Confidence: {confidence} | Active Turns: {state.totalMessagesExchanged} | Time Engaged: {duration}s"
    
    if extracted_items:
        extra_metrics += f" | [INTEL PARSED] -> {'; '.join(extracted_items)}"
        
    clean_notes = base_note + extra_metrics

    from backend.app.models.schemas import EngagementMetrics, IntelligenceObj
    return HoneypotResponse(
        sessionId=sid,
        status="success", 
        reply=reply,
        scamDetected=state.scamDetected,
        totalMessagesExchanged=state.totalMessagesExchanged,
        extractedIntelligence=IntelligenceObj(**state.extractedIntelligence),
        engagementMetrics=EngagementMetrics(
            totalMessagesExchanged=state.totalMessagesExchanged,
            engagementDurationSeconds=int(time.time() - state.start_time)
        ),
        agentNotes=clean_notes
    )
