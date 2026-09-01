import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib
import os
import json
import random

# ─── Feature definitions ───────────────────────────────────────────────────────
# All features that go into the ML model
FEATURE_NAMES = [
    'velocity_1min',          # transactions from this IP in last 1 minute (0–20)
    'velocity_1hr',           # transactions from this card BIN in last 1 hour (0–100)
    'amount_deviation',       # amount / user_30day_average (0.0–10.0, where >5 is spike)
    'hour_of_day',            # 0–23 (2–4am is higher risk)
    'is_foreign_card',        # 0 or 1
    'is_high_risk_bin',       # 0 or 1
    'ip_proxy_flag',          # 0 or 1
    'distance_km_from_last',  # km from last transaction location (0–15000)
    'days_since_account_open' # 0–3000 (newer accounts = higher risk)
]

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'fraud_model.pkl')

def generate_training_data(n_samples: int = 2000) -> pd.DataFrame:
    """Generate realistic synthetic fraud detection dataset."""
    np.random.seed(42)
    random.seed(42)
    
    rows = []
    for i in range(n_samples):
        is_fraud = random.random() < 0.15  # 15% fraud rate
        
        if is_fraud:
            # Fraudulent patterns
            row = {
                'velocity_1min': random.randint(3, 20),
                'velocity_1hr': random.randint(10, 100),
                'amount_deviation': random.uniform(3.0, 10.0),
                'hour_of_day': random.choice([2, 3, 23, 0, 1]),
                'is_foreign_card': random.choices([0, 1], weights=[0.2, 0.8])[0],
                'is_high_risk_bin': random.choices([0, 1], weights=[0.3, 0.7])[0],
                'ip_proxy_flag': random.choices([0, 1], weights=[0.2, 0.8])[0],
                'distance_km_from_last': random.uniform(5000, 15000),
                'days_since_account_open': random.randint(0, 30),
                'label': 1
            }
        else:
            # Legitimate patterns
            row = {
                'velocity_1min': random.randint(0, 2),
                'velocity_1hr': random.randint(0, 5),
                'amount_deviation': random.uniform(0.1, 2.0),
                'hour_of_day': random.randint(8, 22),
                'is_foreign_card': random.choices([0, 1], weights=[0.8, 0.2])[0],
                'is_high_risk_bin': random.choices([0, 1], weights=[0.9, 0.1])[0],
                'ip_proxy_flag': random.choices([0, 1], weights=[0.95, 0.05])[0],
                'distance_km_from_last': random.uniform(0, 500),
                'days_since_account_open': random.randint(100, 3000),
                'label': 0
            }
        rows.append(row)
    
    return pd.DataFrame(rows)

def train_and_save():
    """Train the fraud detection model and save to disk."""
    print("[Shurokkha Sentinel ML] Generating training data...")
    df = generate_training_data(2000)
    
    X = df[FEATURE_NAMES]
    y = df['label']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("[Shurokkha Sentinel ML] Training GradientBoostingClassifier...")
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', GradientBoostingClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42
        ))
    ])
    
    pipeline.fit(X_train, y_train)
    
    y_pred = pipeline.predict(X_test)
    print("\n[Shurokkha Sentinel ML] Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Legit', 'Fraud']))
    
    # Save model
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"[Shurokkha Sentinel ML] Model saved to: {MODEL_PATH}")
    return pipeline

def load_model():
    """Load the trained model. Train if not exists."""
    if not os.path.exists(MODEL_PATH):
        return train_and_save()
    return joblib.load(MODEL_PATH)

# Module-level singleton
_model = None

def _get_model():
    global _model
    if _model is None:
        _model = load_model()
    return _model

def predict_risk(features_dict: dict) -> dict:
    """Predict fraud risk for a transaction.
    
    Args:
        features_dict: Dict with keys matching FEATURE_NAMES
        
    Returns:
        {
            'risk_score': int (0-100),
            'is_fraud_prediction': bool,
            'top_features': list[str]  # top 3 contributing feature names
        }
    """
    model = _get_model()
    
    import pandas as pd
    row = {fname: float(features_dict.get(fname, 0)) for fname in FEATURE_NAMES}
    X = pd.DataFrame([row])
    
    # Get fraud probability
    proba = model.predict_proba(X)[0]  # [prob_legit, prob_fraud]
    fraud_prob = proba[1]
    risk_score = int(fraud_prob * 100)
    
    # Get top contributing features from GBM
    clf = model.named_steps['clf']
    importances = clf.feature_importances_
    top_indices = importances.argsort()[-3:][::-1]
    top_features = [FEATURE_NAMES[i] for i in top_indices]
    
    return {
        'risk_score': risk_score,
        'is_fraud_prediction': bool(model.predict(X)[0] == 1),
        'top_features': top_features
    }


if __name__ == '__main__':
    train_and_save()
    
    # Quick smoke test
    print("\n[Test] Predicting on fraudulent features:")
    fraud_features = {
        'velocity_1min': 15, 'velocity_1hr': 50, 'amount_deviation': 7.5,
        'hour_of_day': 3, 'is_foreign_card': 1, 'is_high_risk_bin': 1,
        'ip_proxy_flag': 1, 'distance_km_from_last': 12000, 'days_since_account_open': 5
    }
    result = predict_risk(fraud_features)
    print(f"  Risk Score: {result['risk_score']}/100")
    print(f"  Is Fraud: {result['is_fraud_prediction']}")
    print(f"  Top Features: {result['top_features']}")
    
    print("\n[Test] Predicting on legitimate features:")
    legit_features = {
        'velocity_1min': 0, 'velocity_1hr': 1, 'amount_deviation': 0.8,
        'hour_of_day': 14, 'is_foreign_card': 0, 'is_high_risk_bin': 0,
        'ip_proxy_flag': 0, 'distance_km_from_last': 50, 'days_since_account_open': 500
    }
    result = predict_risk(legit_features)
    print(f"  Risk Score: {result['risk_score']}/100")
    print(f"  Is Fraud: {result['is_fraud_prediction']}")
    print(f"  Top Features: {result['top_features']}")
