"""
Prediction service. Loads the trained Random Forest / XGBoost models and
region encoder, and exposes a simple predict_emission() function used by
the FastAPI prediction route.

If model artifacts are not found on disk (e.g. fresh clone, before running
`python -m app.ml.train`), this module trains them once automatically so
the API never hard-fails on a missing model file.
"""
import os
import json
import joblib
import numpy as np
import pandas as pd

ML_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(ML_DIR, "model_random_forest.pkl")
XGB_MODEL_PATH = os.path.join(ML_DIR, "model_xgboost.pkl")
ENCODER_PATH = os.path.join(ML_DIR, "region_encoder.pkl")
METRICS_PATH = os.path.join(ML_DIR, "training_metrics.json")

_rf_model = None
_xgb_model = None
_encoder = None
_metrics = None


def _ensure_trained():
    global _rf_model, _xgb_model, _encoder, _metrics
    if not (os.path.exists(MODEL_PATH) and os.path.exists(XGB_MODEL_PATH)
            and os.path.exists(ENCODER_PATH)):
        from app.ml.train import train
        train()

    if _rf_model is None:
        _rf_model = joblib.load(MODEL_PATH)
        _xgb_model = joblib.load(XGB_MODEL_PATH)
        _encoder = joblib.load(ENCODER_PATH)
        with open(METRICS_PATH) as f:
            _metrics = json.load(f)


def _encode_region(region: str) -> int:
    _ensure_trained()
    if region in _encoder.classes_:
        return int(_encoder.transform([region])[0])
    # Unseen region at inference time -> map to closest known class (fallback: 0)
    return 0


def predict_emission(
    cpu_usage: float,
    memory_usage: float,
    storage: float,
    network_traffic: float,
    energy_consumption: float,
    temperature: float,
    region: str,
    horizon_days: int = 7,
    model_name: str = "random_forest",
) -> dict:
    """
    Predicts the carbon emission (kg CO2) `horizon_days` into the future given
    current server telemetry, using the previous emission as `energy_consumption
    * region factor` as a same-day proxy lag feature.
    """
    _ensure_trained()

    from app.ml.carbon_engine import calculate_carbon
    prev_emission_proxy = calculate_carbon(energy_consumption, region)

    region_encoded = _encode_region(region)
    features = pd.DataFrame([{
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage,
        "storage": storage,
        "network_traffic": network_traffic,
        "temperature": temperature,
        "prev_carbon_emission": prev_emission_proxy,
        "region_encoded": region_encoded,
    }])

    model = _xgb_model if model_name == "xgboost" else _rf_model
    base_prediction = float(model.predict(features)[0])

    # Project forward: mild compounding growth assumption based on historical
    # ~0.06%/day infra growth trend baked into the synthetic dataset generator,
    # scaled by the requested horizon.
    growth_factor = 1 + (0.0015 * horizon_days)
    predicted = round(base_prediction * growth_factor, 2)

    confidence = _metrics[model_name if model_name in _metrics else "random_forest"]["confidence_pct"]

    return {
        "predicted_emission_kg": max(0, predicted),
        "confidence": confidence,
        "model_used": model_name,
    }


def get_model_metrics() -> dict:
    _ensure_trained()
    return _metrics
