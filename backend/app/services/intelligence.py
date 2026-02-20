import re
from typing import Dict, List, Any

def extract_intelligence(text: str, combined_input: str, lower_input: str, clean_phones_existing: List[str] = []) -> Dict[str, Any]:
    """Extract ALL possible intelligence from the conversation text."""
    
    # 1. Phone Numbers - Multiple formats including +91-XXXX-XXXXXX, +91 XXXXXXXXXX, etc.
    # Added lookbehinds and lookaheads so we don't extract partial 10 digits from an 18-digit bank account.
    phone_patterns = [
        r'(?<!\d)(?:\+?91[\s\-\.]?)?(?:\(?0?\)?[\s\-\.]?)?[6-9]\d{4}[\s\-\.]?\d{5}(?!\d)',  # Indian mobile
        r'(?<!\d)\+91[\-\s]?\d{10}(?!\d)',  # +91 prefix
        r'(?<!\d)\+91[\-\s]?\d{4}[\-\s]?\d{6}(?!\d)',  # +91-XXXX-XXXXXX
        r'(?<!\d)[6-9]\d{9}(?!\d)',  # Plain 10-digit
    ]
    
    all_phones = set()
    for pattern in phone_patterns:
        found = re.findall(pattern, combined_input)
        for p in found:
            cleaned = p.strip()
            if cleaned:
                all_phones.add(cleaned)
                # Also store just the 10 digits for matching
                digits = re.sub(r'\D', '', cleaned)
                if len(digits) >= 10:
                    all_phones.add(digits[-10:])
                    # Also store with +91 prefix for max compatibility
                    all_phones.add('+91-' + digits[-10:])
    
    # Remove phones that match existing to avoid dedup issues
    clean_phones = list(all_phones)
    
    # 2. Bank Accounts - Any long digit sequence (10-18 digits)
    potential_accounts = list(set(re.findall(r'\b\d{10,18}\b', combined_input)))
    # Filter out anything that's just a phone number
    phone_digits = {re.sub(r'\D', '', p)[-10:] for p in all_phones if len(re.sub(r'\D', '', p)) >= 10}
    safe_accounts = [acc for acc in potential_accounts if acc[-10:] not in phone_digits]
    
    # 3. UPI IDs - Must have @ but exclude normal email domains
    email_domains = {'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'protonmail.com', 'mail.com', 'live.com', 'icloud.com', 'aol.com', 'rediffmail.com'}
    all_at_ids = re.findall(r'[\w\.\-]+@[\w\.\-]+', combined_input)
    
    upi_ids = []
    email_addresses = []
    for aid in all_at_ids:
        domain = aid.split('@')[-1].lower()
        # If domain has no dots or is a known UPI handle, it's UPI
        if '.' not in domain or domain in ['okaxis', 'okhdfcbank', 'okicici', 'oksbi', 'ybl', 'paytm', 'upi', 'apl', 'ibl', 'axl']:
            upi_ids.append(aid)
        elif domain.lower() in email_domains:
            email_addresses.append(aid)
        else:
            # Could be either— check if it looks like a legit email 
            if domain.count('.') >= 1 and len(domain) > 4:
                email_addresses.append(aid)
            else:
                upi_ids.append(aid)
    
    # 4. Phishing Links
    links = re.findall(r'https?://[^\s<>"\']+', combined_input)
    # Also catch shortened/suspicious links
    links += re.findall(r'(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl)/\S+', lower_input)
    
    # 5. Suspicious Keywords
    keyword_list = ["verify", "blocked", "urgent", "otp", "kyc", "compromised", "lock", "suspend",
                    "arrest", "warrant", "police", "cbi", "customs", "seized",
                    "job", "part time", "work from home", "salary", "daily income", "investment",
                    "win", "lottery", "prize", "cashback", "refund", "claim",
                    "bank", "sbi", "hdfc", "icici", "axis", "kotak", "pnb"]
    
    # 6. Official IDs / Reference Numbers
    # Matches patterns like SBI-12345, ID: 8492, Ref No: 9283, Employee Code: 4821
    id_patterns = [
        r'\b(?:ID|Ref|Code|Officer|Employee)\s?(?:ID|No|Number|#)?[:.\-]?\s?([A-Z0-9\-]{4,15})\b',
        r'\b(?:[A-Z]{2,4}-\d{4,8})\b', # SBI-12345 style
    ]
    all_ids = set()
    for pattern in id_patterns:
        # Use simple lowercase search for keywords but keep case for the ID itself
        found = re.finditer(pattern, text, re.IGNORECASE)
        for match in found:
            # If the pattern has groups, take the first one, else the full match
            val = match.group(1) if match.groups() else match.group()
            # Clean up and avoid adding phone numbers as IDs
            val_clean = val.strip().rstrip('.,')
            if len(re.sub(r'\D', '', val_clean)) < 10: # Likely not a phone
                all_ids.add(val_clean)
    
    
    found_keywords = list(set([k for k in keyword_list if k in lower_input]))
    
    return {
        "bankAccounts": safe_accounts,
        "upiIds": list(set(upi_ids)),
        "phishingLinks": list(set(links)),
        "phoneNumbers": clean_phones,
        "emailAddresses": list(set(email_addresses)),
        "officialIds": list(all_ids),
        "suspiciousKeywords": found_keywords
    }

def calculate_scam_score(text: str, intel: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate a scam risk score based on weighted indicators.
    Returns a dict with 'score', 'risk_level', 'reasons', and 'attack_type'.
    """
    score = 0
    reasons = []
    lower = text.lower()
    
    # --- WEIGHTED INDICATORS ---
    weights = {
        "high": 50,    # Immediate critical threats (OTP, PIN, Remote Access)
        "medium": 30,  # Standard scam tactics (KYC, Block, Lottery)
        "low": 10,     # Pressure tactics (Urgent, Offer)
        "entity": 20   # Suspicious entities present
    }
    
    # 1. High Risk Keywords
    high_risk_triggers = [
        "otp", "pin", "password", "cvv", "anydesk", "teamviewer", "quicksupport", 
        "screen share", "apk", "install", "download", "refund", "cbi", "police", 
        "arrest", "warrant", "drugs", "customs", "seized"
    ]
    for k in high_risk_triggers:
        if k in lower:
            score += weights["high"]
            reasons.append(f"High-Risk Trigger: {k}")
            break # Cap per category to avoid double counting same trigger type

    # 2. Medium Risk Keywords
    medium_risk_triggers = [
        "kyc", "verify", "block", "suspend", "expiry", "update", "pan card", "aadhaar", 
        "lottery", "winner", "prize", "job", "salary", "investment", "cryptocurrency", 
        "bit.ly", "tinyurl", "shorts"
    ]
    match_med = [k for k in medium_risk_triggers if k in lower]
    if match_med:
        score += weights["medium"]
        reasons.append(f"Medium-Risk Triggers: {', '.join(match_med[:2])}")

    # 3. Low Risk Keywords (Pressure/Lure)
    low_risk_triggers = [
        "urgent", "immediately", "today", "offer", "limited", "hurry", "fast", 
        "sir", "madam", "dear customer"
    ]
    if any(k in low_risk_triggers for k in lower):
        score += weights["low"]
        reasons.append("Pressure/Lure tactics detected")

    # 4. Entity Analysis
    if intel.get("phishingLinks"):
        score += 40
        reasons.append("Phishing Link Detected")
    
    if intel.get("bankAccounts"):
        score += 30
        reasons.append("Bank Account Solicitation")
        
    if intel.get("upiIds"):
        score += 20
        reasons.append("UPI Payment Request")

    # 5. Contextual Heuristics
    # Asking for money/transfer
    if re.search(r'\b(pay|transfer|send|deposit|scan|qr)\b', lower):
        score += 20
        reasons.append("Payment Request Detected")
        
    # Isolation tactics
    if re.search(r'\b(alone|tell no one|secret|private)\b', lower):
        score += 30
        reasons.append("Isolation Tactic Detected")

    # --- CLASSIFICATION ---
    risk_level = "LOW"
    if score >= 80: risk_level = "CRITICAL"
    elif score >= 50: risk_level = "HIGH"
    elif score >= 20: risk_level = "MEDIUM"

    # Determine Likely Attack Type
    attack_type = "Generic Suspicious Activity"
    if re.search(r'\b(otp|pin|cvv|scan|pay)\b', lower) or intel.get("bankAccounts"):
        attack_type = "Financial Fraud"
    elif re.search(r'\b(police|cbi|arrest|drugs|customs)\b', lower):
        attack_type = "Digital Arrest / Impersonation"
    elif re.search(r'\b(lottery|win|prize|job|invest)\b', lower):
        attack_type = "Temptation / Investment Scam"
    elif intel.get("phishingLinks") or re.search(r'\b(apk|app)\b', lower):
        attack_type = "Phishing / Malware"
    elif re.search(r'\b(kyc|update|pan|aadhaar)\b', lower):
        attack_type = "KYC Fraud"

    return {
        "score": min(score, 100),  # Cap at 100
        "risk_level": risk_level,
        "scam_detected": score >= 40, # Threshold for active defense
        "reasons": reasons,
        "attack_type": attack_type
    }

def extract_conversation_focus(text: str) -> str:
    """
    Heuristically extracts the main topic/subject of the scam message 
    to allow for dynamic, investigative questioning.
    """
    stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'to', 'for', 'of', 'in', 'on', 'at', 'by', 'your', 'my', 'is', 'urgent', 'immediately', 'kindly', 'please', 'verify', 'click', 'link', 'account'}
    
    # 1. Look for Proper Nouns / Capitalized Phrases (e.g., "Netflix Premium", "CBI Officer", "FedEx")
    # pattern: Capitalized word, optionally followed by more capitalized words
    cap_phrases = re.findall(r'(?:[A-Z][a-z]+\s?)+', text)
    # Filter out common starters like "Dear Customer" or "Start" if they are just single words
    meaningful_caps = [p.strip() for p in cap_phrases if len(p.strip()) > 3 and p.lower() not in stopwords]
    
    if meaningful_caps:
        # Return the longest customized phrase as it's likely the specific entity
        return max(meaningful_caps, key=len)

    # 2. Look for words after action verbs (payment for X, download X)
    action_match = re.search(r'\b(pay|download|install|verify|update|blocked)\s+([a-zA-Z]+)', text.lower())
    if action_match and action_match.group(2) not in stopwords:
        return action_match.group(2)

    # 3. Fallback: Find the most "complex" word (longest distinct word)
    words = re.findall(r'\b\w+\b', text)
    valid_words = [w for w in words if w.lower() not in stopwords and len(w) > 4 and not w.isdigit()]
    if valid_words:
        return max(valid_words, key=len)
        
    return "this matter"
