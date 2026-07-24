import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import MinMaxScaler
import joblib
import os

FEATURES = ['temperature', 'utilization', 'memory_used', 'power_draw']
MODEL_IF_PATH = "models/isolation_forest.pkl"
MODEL_RF_PATH = "models/random_forest.pkl"
SCALER_PATH = "models/scaler.pkl"

scaler = MinMaxScaler()
iso_forest = None
rf_model = None

def _generate_training_data(n=500):
    normal = pd.DataFrame({
        'temperature': np.random.uniform(40, 80, n),
        'utilization': np.random.uniform(20, 90, n),
        'memory_used': np.random.uniform(10, 60, n),
        'power_draw': np.random.uniform(100, 300, n),
    })
    normal['label'] = 0

    anomaly = pd.DataFrame({
        'temperature': np.random.uniform(88, 98, n // 5),
        'utilization': np.random.uniform(0, 3, n // 5),
        'memory_used': np.random.uniform(70, 80, n // 5),
        'power_draw': np.random.uniform(380, 420, n // 5),
    })
    anomaly['label'] = 1

    return pd.concat([normal, anomaly], ignore_index=True).sample(frac=1)

def train_models():
    global iso_forest, rf_model, scaler
    os.makedirs("models", exist_ok=True)

    df = _generate_training_data()
    X = df[FEATURES].values
    y = df['label'].values

    scaler.fit(X)
    X_scaled = scaler.transform(X)

    iso_forest = IsolationForest(contamination=0.1, random_state=42)
    iso_forest.fit(X_scaled)

    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_scaled, y)

    joblib.dump(iso_forest, MODEL_IF_PATH)
    joblib.dump(rf_model, MODEL_RF_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print("Models trained and saved.")

def load_models():
    global iso_forest, rf_model, scaler
    if os.path.exists(MODEL_IF_PATH):
        iso_forest = joblib.load(MODEL_IF_PATH)
        rf_model = joblib.load(MODEL_RF_PATH)
        scaler = joblib.load(SCALER_PATH)
    else:
        train_models()

def predict_risk(metrics_df):
    global iso_forest, rf_model, scaler
    if iso_forest is None:
        load_models()

    X = metrics_df[FEATURES].values
    X_scaled = scaler.transform(X)

    if_scores = iso_forest.decision_function(X_scaled)
    if_scores_norm = 1 - (if_scores - if_scores.min()) / (if_scores.max() - if_scores.min() + 1e-9)

    rf_probs = rf_model.predict_proba(X_scaled)[:, 1]

    combined = (if_scores_norm * 0.5 + rf_probs * 0.5) * 100

    results = []
    for i, row in metrics_df.iterrows():
        score = round(float(combined[i]), 1)
        if score < 40:
            level = "Normal"
        elif score < 70:
            level = "Warning"
        else:
            level = "Critical"

        # Calculate Explainable AI (XAI) Root Cause Breakdown
        # Find which metric contributed most to the risk
        temp_ratio = max(0, (row['temperature'] - 70) / 30)
        util_ratio = max(0, (row['utilization'] - 85) / 15) if row['utilization'] > 85 else (1.0 if row['utilization'] < 5 and row['temperature'] > 60 else 0)
        mem_ratio = max(0, (row['memory_used'] - 60) / 20)
        power_ratio = max(0, (row['power_draw'] - 280) / 120)

        causes = []
        if row['temperature'] >= 80:
            causes.append(f"Thermal Spike ({row['temperature']}°C)")
        if row['power_draw'] >= 320:
            causes.append(f"Power Surge ({row['power_draw']}W)")
        if row['memory_used'] >= 65:
            causes.append(f"High VRAM Load ({row['memory_used']} GB)")
        if row['utilization'] < 5 and row['temperature'] > 60:
            causes.append(f"Idle Thermal Anomaly (0% Load, High Temp)")

        root_cause = ", ".join(causes) if causes else "Healthy / Nominal Operation"

        results.append({
            'node_id': int(row['node_id']),
            'risk_score': score,
            'risk_level': level,
            'root_cause': root_cause
        })

    return pd.DataFrame(results)
