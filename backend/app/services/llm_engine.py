from langchain_openai import ChatOpenAI
from backend.app.core.config import OPENAI_API_KEY, SHIELD_KEY, is_valid_sk

# Select LLM - Strictly OpenAI
default_llm = None
if is_valid_sk(OPENAI_API_KEY):
    try:
        print("Initializing OpenAI (ChatGPT) LLM...")
        default_llm = ChatOpenAI(model="gpt-4o", openai_api_key=OPENAI_API_KEY, temperature=0.9)
    except Exception as e:
        print(f"Error initializing OpenAI: {e}")

# --- ABSOLUTE PROJECT SHIELD (Final Safety Net) ---
if not default_llm:
    print("🛡️ ACTIVATING PROJECT SHIELD: Environment keys invalid. Using hardcoded brain.")
    default_llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=SHIELD_KEY, temperature=0.7)

def get_llm(auth_key: str = None):
    """
    Returns the appropriate LLM instance based on auth key or fallback.
    """
    # 1. Try Dynamic Header (Postman key)
    if auth_key and is_valid_sk(auth_key):
        try: 
            return ChatOpenAI(model="gpt-4o", openai_api_key=auth_key, temperature=0.7)
        except: 
            pass
    
    # 2. Return Default (Master or Shield)
    return default_llm
