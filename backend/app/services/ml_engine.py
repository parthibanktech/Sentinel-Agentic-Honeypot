import os
import pickle
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline

def find_file(filename):
    """Search for a file in multiple locations."""
    search_paths = [
        filename,
        os.path.join("backend", filename),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), filename),
        os.path.join("/app/backend", filename)
    ]
    for p in search_paths:
        if os.path.exists(p):
            return p
    return filename # Fallback to filename in CWD

ML_MODEL_PATH = find_file("sentinel_model.pkl")
DATASET_PATH = find_file("scam_dataset.json")

def load_training_data():
    """
    Loads training data from external source (JSON or CSV) or generates a robust base detailed set if data is missing.
    """
    # Check current directory
    paths_to_check = ["scam_dataset.json", "backend/scam_dataset.json", "../scam_dataset.json"]
    
    for path in paths_to_check:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    print(f"📊 Loading External Dataset from: {path}")
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading dataset {path}: {e}")
    
    # PROCEDURAL DATA GENERATION (Base Knowledge) as Fallback
    print("⚠️ No external dataset found. Generating ROBUST procedural training set (v2.0).")
    dataset = []
    
    # --- SCAM TEMPLATES ---
    # 1. Financial / Urgency
    financial_prefixes = ["Dear Customer,", "Alert:", "Warning:", "SBI Bank:", "HDFC Alert:", "Last Reminder:", "URGENT:", "RBI Notification:"]
    financial_actions = ["KYC update pending", "PAN card expired", "Account blocked within 24hrs", "Debit card suspended", "Sim card verification pending", "Electricity bill unpaid", "Credit points expiring"]
    financial_calls = ["Click here t.ly/xyz", "Call immediately 98xxxx", "Update now bit.ly/bank", "Verify at secure-bank.com", "Download QuickSupport app"]
    
    for p in financial_prefixes:
        for a in financial_actions:
            for c in financial_calls:
                dataset.append((f"{p} {a}. {c}", 1))

    # 2. Authority / Fear (Digital Arrest)
    auth_actors = ["CBI Officer", "Mumbai Police", "Customs Dept", "Narcotics Bureau", "Fedex Courier", "TRAI Official"]
    auth_claims = ["illegal parcel in your name", "drugs found in package", "money laundering case registered", "warrant issued against you", "mobile number disconnecting in 2 hours"]
    auth_threats = ["You will be arrested.", "Come to station immediately.", "Join video call for verification.", "Pay fine to avoid jail.", "Do not disconnect call."]
    
    for a in auth_actors:
        for c in auth_claims:
            for t in auth_threats:
                dataset.append((f"This is {a}. {c}. {t}", 1))

    # 3. Greed / Job / Investment
    greed_hooks = ["Congratulations!", "Part time job offer:", "Work from home:", "Investment Opportunity:", "Lottery Winner:"]
    greed_promises = ["Earn 5000/day", "Double your money in 3 days", "Guaranteed returns 20%", "Win iPhone 15", "Salary 1 lakh/month"]
    greed_actions = ["Join Telegram group.", "Deposit 1000rs registration.", "Click link to claim.", "Message for details."]
    
    for h in greed_hooks:
        for p in greed_promises:
            for a in greed_actions:
                dataset.append((f"{h} {p}. {a}", 1))

    # 4. Family / Emergency (Impersonation)
    fam_intros = ["Hi dad,", "Hello mom,", "Hey friend,", "Hi uncle,"]
    fam_situations = ["I lost my phone.", "I am in hospital.", "Stuck in airport.", "Need urgent money for ticket."]
    fam_demands = ["Send 5000 to this UPI.", "Transfer via GPay fast.", "Scan this QR code.", "Help me please."]
    
    for i in fam_intros:
        for s in fam_situations:
            for d in fam_demands:
                dataset.append((f"{i} {s} {d}", 1))

    # --- BENIGN templates (To prevent False Positives) ---
    benign_intros = ["Hi,", "Hello,", "Hey,", "Good morning,", "Dear sir,"]
    benign_content = ["meeting is at 5pm", "can we reschedule?", "happy birthday!", "where are you?", "package delivered securely to security", "your transaction of 500rs is successful", "OTP for login is 1234 (do not share)"]
    benign_closings = ["Thanks.", "See you.", "Call me.", "Ok.", "Cheers."]
    
    for i in benign_intros:
        for c in benign_content:
            for cl in benign_closings:
               dataset.append((f"{i} {c}. {cl}", 0))

    # Add specific realistic hard negatives (tricky cases)
    hard_negatives = [
        ("Your SBI transaction of Rs 500 is successful. Ref: 12345", 0),
        ("HDFC Bank: OTP for transaction is 849201. Do not share this with anyone.", 0),
        ("Police advise: Do not share OTP or passwords with strangers.", 0),
        ("Job interview scheduled for Monday 10am at office.", 0),
        ("Can you pay the electricity bill? I forgot.", 0),
        ("I will transfer the money to you tomorrow.", 0)
    ]
    dataset.extend(hard_negatives)

    print(f"📚 Generated {len(dataset)} varied training samples for Robust Generic Detection.")
    return dataset

def train_sentinel_model():
    print("🧠 Training Sentinel Advanced Ensemble Model (Voting Classifier)...")
    
    # Load dynamic data
    data = load_training_data()
    texts, labels = zip(*data)
    
    # 1. Linear Logic (Speed)
    clf1 = LogisticRegression(random_state=42)
    # 2. Decision Trees (Non-linear complexity)
    clf2 = RandomForestClassifier(n_estimators=50, random_state=42)
    # 3. Support Vector Machine (High-dimensional accuracy)
    clf3 = SVC(probability=True, random_state=42)
    
    # ENSEMBLE: Combine all 3 "brains"
    voting_clf = VotingClassifier(
        estimators=[('lr', clf1), ('rf', clf2), ('svm', clf3)],
        voting='soft'
    )
    
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1,3), min_df=1)), 
        ('ensemble', voting_clf)
    ])
    pipeline.fit(texts, labels)
    
    with open(ML_MODEL_PATH, "wb") as f:
        pickle.dump(pipeline, f)
    
    print("✅ Sentinel Ensemble Model (LR+RF+SVM) Trained & Loaded.")
    return pipeline

ml_pipeline = None

# Initialize Model
if os.path.exists(ML_MODEL_PATH):
    try:
        with open(ML_MODEL_PATH, "rb") as f:
            ml_pipeline = pickle.load(f)
    except:
        ml_pipeline = train_sentinel_model()
else:
    ml_pipeline = train_sentinel_model()

def predict_scam_ml(text):
    if not ml_pipeline: return False, 0.0
    try:
        prob = ml_pipeline.predict_proba([text])[0][1]
        return prob > 0.6, prob
    except:
        return False, 0.0
