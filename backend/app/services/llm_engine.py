import asyncio
import time
from openai import AsyncOpenAI
import google.generativeai as genai
from backend.app.core.config import OPENAI_API_KEY, GOOGLE_API_KEY, SHIELD_KEY, is_valid_sk, is_valid_google

# --- CONFIG ---
_openai_key = OPENAI_API_KEY if is_valid_sk(OPENAI_API_KEY) else SHIELD_KEY
_google_key = GOOGLE_API_KEY if is_valid_google(GOOGLE_API_KEY) else None

# Initialize Clients
_openai_client = AsyncOpenAI(api_key=_openai_key, max_retries=1, timeout=10.0)
if _google_key:
    genai.configure(api_key=_google_key)
    _gemini_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    _gemini_model = None

async def call_llm_openai(prompt: str) -> str:
    response = await _openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=100,
    )
    return response.choices[0].message.content.strip()

async def call_llm_gemini(prompt: str) -> str:
    if not _gemini_model:
        raise Exception("Gemini not configured")
    # Wrap blocking genai call in thread
    response = await asyncio.to_thread(_gemini_model.generate_content, prompt)
    return response.text.strip()

async def call_llm(prompt: str) -> str:
    """Primary LLM caller with auto-fallback between OpenAI and Gemini."""
    t = time.time()
    
    # Strategy: Try OpenAI first (primary), fallback to Gemini
    try:
        result = await call_llm_openai(prompt)
        print(f"[LLM] OpenAI: {time.time()-t:.2f}s")
        return result
    except Exception as e:
        print(f"[LLM] OpenAI Failed: {e}. Trying Gemini...")
        
    if _gemini_model:
        try:
            result = await call_llm_gemini(prompt)
            print(f"[LLM] Gemini: {time.time()-t:.2f}s")
            return result
        except Exception as e:
            print(f"[LLM] Gemini Failed: {e}")
            
    return "Error: All LLM engines failed."

# Warm up
async def _warmup():
    try:
        await _openai_client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":"Hi"}], max_tokens=5)
        print("[LLM] OpenAI Warmup OK")
    except: pass

print(f"[LLM] Hybrid Engine Loaded (OpenAI Target: ...{_openai_key[-6:]}, Gemini Active: {bool(_gemini_model)})")
