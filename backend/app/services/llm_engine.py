import time
from openai import AsyncOpenAI
from backend.app.core.config import OPENAI_API_KEY, SHIELD_KEY, is_valid_sk

def _get_key(auth_key: str = None) -> str:
    if auth_key and is_valid_sk(auth_key):
        return auth_key
    if is_valid_sk(OPENAI_API_KEY):
        return OPENAI_API_KEY
    return SHIELD_KEY

# Pre-create client at startup with connection pooling
_default_key = _get_key()
_client = AsyncOpenAI(api_key=_default_key, max_retries=1, timeout=10.0)

async def call_llm(prompt: str, auth_key: str = None) -> str:
    """Direct OpenAI call via official SDK. Fastest possible."""
    key = _get_key(auth_key)
    t = time.time()
    
    # Use default client if key matches, else create temporary
    client = _client if key == _default_key else AsyncOpenAI(api_key=key, max_retries=1, timeout=10.0)
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=80,
    )
    
    result = response.choices[0].message.content.strip()
    elapsed = time.time() - t
    print(f"[LLM] {elapsed:.2f}s | {len(result)} chars")
    return result

# Warm up: make a preflight request at startup to establish connection
async def _warmup():
    try:
        await _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5,
        )
        print("[LLM] Warmup complete - connection pool ready")
    except:
        print("[LLM] Warmup failed (non-critical)")

print(f"[LLM] OpenAI SDK engine loaded (key: ...{_default_key[-8:]})")
