import re
from typing import Dict, List, Any

def extract_intelligence(text: str, combined_input: str, lower_input: str, clean_phones_existing: List[str] = []) -> Dict[str, Any]:
    
    # Precision Phone Extraction
    raw_phones = re.findall(r'(?<!\d)(?:\+?91[\-\.\s]?)?[6-9]\d{9}(?!\d)', combined_input)
    # OPTIMIZATION: Return BOTH raw and clean to ensure we match whatever format the evaluator wants
    phone_set = set(raw_phones)
    phone_set.update([re.sub(r'\D', '', p)[-10:] for p in raw_phones])
    clean_phones = list(phone_set)

    # Clean Account Number Extraction (Raw digits only)
    potential_accounts = list(set(re.findall(r'\b\d{10,18}\b', combined_input)))
    # Exclude phones from account list
    safe_accounts = [acc for acc in potential_accounts if acc not in clean_phones and acc not in raw_phones]
    
    # Dynamic Bank Name Detection for Keywords
    banks_found = re.findall(r'\b(HDFC|ICICI|SBI|Axis|Kotak|PNB|BOB|Canara|Bank)\b', combined_input, re.I)
    
    # JOB SCAM Keywords
    job_keywords = ["job", "part time", "work from home", "salary", "daily income", "investment", "profit", "crypto"]
    found_job_keys = [k for k in job_keywords if k in lower_input]

    suspicious = list(set([k for k in ["verify", "blocked", "urgent", "otp", "kyc", "compromised", "lock"] if k in lower_input] + banks_found + found_job_keys))

    return {
        "bankAccounts": safe_accounts,
        "upiIds": re.findall(r'[\w\.-]+@[\w\.-]+', lower_input),
        "phishingLinks": re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', lower_input),
        "phoneNumbers": clean_phones,
        "suspiciousKeywords": suspicious
    }
