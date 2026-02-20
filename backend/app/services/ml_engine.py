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
    EXPERIMENTAL: Loads training data.
    """
    if os.path.exists(DATASET_PATH):
        try:
            with open(DATASET_PATH, 'r') as f:
                print(f"📊 Loading External Dataset from: {DATASET_PATH}")
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading dataset: {e}")
    
    # Final Fallback
    dataset = []
    return [
        ("URGENT: Your account is blocked. Click bit.ly/123", 1),
        ("Hello, how are you today?", 0)
    ]

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
