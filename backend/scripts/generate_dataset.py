import json
import os

def generate_procedural_dataset():
    """
    Generates a robust, generic scam dataset using combinatorial templates.
    This ensures the ML model learns patterns rather than specific hardcoded messages.
    """
    dataset = []
    
    # 1. Financial / Urgency Scams (The "Lure")
    prefixes = ["Dear Customer,", "Alert:", "Warning:", "SBI Bank:", "HDFC Alert:", "URGENT:", "RBI Notification:"]
    actions = ["KYC update pending", "PAN card expired", "Account blocked within 24hrs", "Debit card suspended", "Electricity bill unpaid"]
    calls = ["Click here t.ly/xyz", "Call immediately 98xxxx", "Update now bit.ly/bank", "Verify at secure-bank.com"]
    
    for p in prefixes:
        for a in actions:
            for c in calls:
                dataset.append((f"{p} {a}. {c}", 1))

    # 2. Authority / Fear (Digital Arrest)
    actors = ["CBI Officer", "Mumbai Police", "Customs Dept", "Narcotics Bureau", "Fedex Courier"]
    claims = ["illegal parcel in your name", "drugs found in package", "warrant issued against you", "mobile number disconnecting in 2 hours"]
    threats = ["You will be arrested.", "Come to station immediately.", "Pay fine to avoid jail.", "Do not disconnect call."]
    
    for a in actors:
        for c in claims:
            for t in threats:
                dataset.append((f"This is {a}. {c}. {t}", 1))

    # 3. Greed / Job ऑफर्स
    hooks = ["Congratulations!", "Part time job offer:", "Work from home:", "Investment Opportunity:", "Lottery Winner:"]
    promises = ["Earn 5000/day", "Double your money in 3 days", "Win iPhone 15", "Salary 1 lakh/month"]
    actions_greed = ["Join Telegram group.", "Deposit 1000rs registration.", "Click link to claim."]
    
    for h in hooks:
        for p in promises:
            for a in actions_greed:
                dataset.append((f"{h} {p}. {a}", 1))

    # 4. Benign Samples (To prevent False Positives)
    benign_intros = ["Hi,", "Hello,", "Hey,", "Good morning,"]
    benign_content = ["meeting is at 5pm", "can we reschedule?", "happy birthday!", "where are you?", "your transaction of 500rs is successful"]
    benign_closings = ["Thanks.", "See you.", "Ok.", "Cheers."]
    
    for i in benign_intros:
        for c in benign_content:
            for cl in benign_closings:
               dataset.append((f"{i} {c}. {cl}", 0))

    # 5. Hard Negatives (Tricky non-scam cases)
    hard_negatives = [
        ("Your SBI transaction of Rs 500 is successful. Ref: 12345", 0),
        ("HDFC Bank: OTP for transaction is 849201. Do not share this with anyone.", 0),
        ("Police advise: Do not share OTP or passwords with strangers.", 0),
        ("Job interview scheduled for Monday 10am at office.", 0),
        ("Can you pay the electricity bill? I forgot.", 0),
        ("Meeting with the CBI consultant regarding tax compliance.", 0)
    ]
    dataset.extend(hard_negatives)

    output_path = "scam_dataset.json"
    with open(output_path, 'w') as f:
        json.dump(dataset, f, indent=2)
    
    print(f"✅ Generated {len(dataset)} generic training samples in {output_path}")

if __name__ == "__main__":
    generate_procedural_dataset()
