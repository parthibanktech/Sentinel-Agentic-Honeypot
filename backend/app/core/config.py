import os
from dotenv import load_dotenv

load_dotenv()

HONEYPOT_API_KEY = os.getenv("HONEYPOT_API_KEY", "sentinel-master-key")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY") 
CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

SHIELD_KEY = "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"

def is_valid_sk(k): 
    return isinstance(k, str) and k.startswith("sk-") and len(k) > 30 and "{" not in k and "$" not in k
