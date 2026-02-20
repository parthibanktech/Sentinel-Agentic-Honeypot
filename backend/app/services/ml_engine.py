import os
import pickle
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline

ML_MODEL_PATH = "sentinel_model.pkl"
DATASET_PATH = "scam_dataset.json"

def load_training_data():
    """
    Loads training data from external source or generates a robust base set.
    """
    if os.path.exists(DATASET_PATH):
        try:
            with open(DATASET_PATH, 'r') as f:
                return json.load(f)
        except:
            pass
    
    # PROCEDURAL DATA GENERATION (Base Knowledge)
    dataset = []
    
    # 1. Bank Fraud Patterns
    bank_phrases = ["KYC", "PAN card", "block", "verify", "update", "expiry", "debit card", "credit card", "points"]
    for p in bank_phrases:
         dataset.append((f"Your {p} is pending update. Click link.", 1))
         dataset.append((f"Alert: Your account {p} issue resolved.", 0)) # False positive check

    # 2. Job Scam Patterns
    job_phrases = ["part time", "work from home", "daily income", "easy money", "investment", "multiply"]
    for p in job_phrases:
        dataset.append((f"Start {p} and earn 5000 daily.", 1))
        
    # 3. Urgent/Authority Patterns
    urgent_phrases = ["police", "CBI", "arrest", "warrant", "customs", "illegal", "seized"]
    for p in urgent_phrases:
        dataset.append((f"This is {p} department. You are under surveillance.", 1))
        
    # 4. Generics
    benign = [
        "Hi, how are you?", "Did you eat?", "Where are you?", "Call me back.", "Meeting at 5.",
        "Happy birthday!", "See you soon.", "Okay, thanks.", "No problem.", "What is the update?"
    ]
    for b in benign:
        dataset.append((b, 0))
    
    # Extended real-world scam indicators
    data = [
        ("Your SBI account is blocked. Click here.", 1),
        ("You have won a lottery of 5 crores.", 1),
        ("Verify your KYC immediately.", 1),
        ("Hi, how are you?", 0),
        ("Can we meet for coffee?", 0),
        ("Your package is pending delivery.", 1),
        ("Investment opportunity double money.", 1),
        ("Job offer work from home salary 50000.", 1),
        ("Is this the right number?", 0),
        ("Happy birthday my friend.", 0),
        ("Urgent electricity bill unpaid.", 1),
        ("Credit card points expiring redeem now.", 1),
        ("Hey, long time no see.", 0),
        ("Dinner tonight?", 0),
        ("Police case registered against you.", 1),
        ("CBI investigation warrant issued.", 1),
        ("Dad, I lost my phone, send money.", 1),
        ("Good morning, have a nice day.", 0)
    ]
    dataset.extend(data)
        
    print(f"📚 Loaded {len(dataset)} training samples for core engine.")
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
