"""
ML Training Pipeline for Carbon Emission Forecasting.

Pipeline stages:
    Dataset -> Data Cleaning -> Feature Engineering -> Train/Test Split ->
    Model Training (Random Forest + XGBoost) -> Evaluation -> Model Saving

Run directly:  python -m app.ml.train
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score
import xgboost as xgb

from app.ml.generate_dataset import generate

FEATURES = [
    "cpu_usage", "memory_usage", "storage", "network_traffic",
    "temperature", "prev_carbon_emission", "region_encoded",
]
TARGET = "carbon_emission"

ML_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(ML_DIR, "model_random_forest.pkl")
XGB_MODEL_PATH = os.path.join(ML_DIR, "model_xgboost.pkl")
ENCODER_PATH = os.path.join(ML_DIR, "region_encoder.pkl")
METRICS_PATH = os.path.join(ML_DIR, "training_metrics.json")


def load_data() -> pd.DataFrame:
    dataset_path = os.path.abspath(os.path.join(ML_DIR, "..", "..", "..", "dataset",
                                                 "cloud_emissions_dataset.csv"))
    if os.path.exists(dataset_path):
        return pd.read_csv(dataset_path)
    print("Dataset not found on disk, generating synthetic dataset in-memory...")
    return generate()


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["cpu_usage", "memory_usage", "energy_consumption", TARGET])
    df = df[(df["cpu_usage"] >= 0) & (df["cpu_usage"] <= 100)]
    df = df[(df["memory_usage"] >= 0) & (df["memory_usage"] <= 100)]
    df = df[df[TARGET] >= 0]
    return df.reset_index(drop=True)


def feature_engineer(df: pd.DataFrame, encoder: LabelEncoder = None):
    if encoder is None:
        encoder = LabelEncoder()
        df["region_encoded"] = encoder.fit_transform(df["region"])
    else:
        df["region_encoded"] = encoder.transform(df["region"])
    return df, encoder


def train():
    print("Step 1/6: Loading dataset...")
    df = load_data()

    print("Step 2/6: Cleaning data...")
    df = clean_data(df)

    print("Step 3/6: Feature engineering...")
    df, encoder = feature_engineer(df)

    X = df[FEATURES]
    y = df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Step 4/6: Training Random Forest model...")
    rf = RandomForestRegressor(
        n_estimators=250, max_depth=12, min_samples_leaf=3,
        random_state=42, n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)
    rf_mae = mean_absolute_error(y_test, rf_pred)
    rf_r2 = r2_score(y_test, rf_pred)

    print("Step 4b/6: Training XGBoost model...")
    xgb_model = xgb.XGBRegressor(
        n_estimators=300, max_depth=6, learning_rate=0.05,
        subsample=0.9, colsample_bytree=0.9, random_state=42,
    )
    xgb_model.fit(X_train, y_train)
    xgb_pred = xgb_model.predict(X_test)
    xgb_mae = mean_absolute_error(y_test, xgb_pred)
    xgb_r2 = r2_score(y_test, xgb_pred)

    print("Step 5/6: Saving models...")
    joblib.dump(rf, MODEL_PATH)
    joblib.dump(xgb_model, XGB_MODEL_PATH)
    joblib.dump(encoder, ENCODER_PATH)

    metrics = {
        "random_forest": {
            "mae_kg_co2": round(float(rf_mae), 3),
            "r2_score": round(float(rf_r2), 4),
            "confidence_pct": round(max(0, min(99, rf_r2 * 100)), 1),
        },
        "xgboost": {
            "mae_kg_co2": round(float(xgb_mae), 3),
            "r2_score": round(float(xgb_r2), 4),
            "confidence_pct": round(max(0, min(99, xgb_r2 * 100)), 1),
        },
        "n_train_rows": len(X_train),
        "n_test_rows": len(X_test),
        "features": FEATURES,
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    print("Step 6/6: Done.")
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    train()
