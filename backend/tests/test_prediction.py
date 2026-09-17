import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def auth_token():
    creds = {"name": "Predictor", "email": "predictor@example.com", "password": "PredictPass1"}
    client.post("/api/auth/register", json=creds)
    resp = client.post("/api/auth/login", json={"email": creds["email"], "password": creds["password"]})
    return resp.json()["access_token"]


def test_predict_endpoint_returns_emission(auth_token):
    """
    NOTE: first call triggers on-demand model training (see app/ml/predict.py
    _ensure_trained), so this test may take longer on a cold run.
    """
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {
        "server_id": "AWS001",
        "cpu_usage": 80,
        "memory_usage": 70,
        "storage": 400,
        "network_traffic": 50,
        "energy_consumption": 300,
        "temperature": 24,
        "region": "ap-south-1",
        "horizon_days": 7,
        "model_name": "random_forest",
    }
    resp = client.post("/api/predict/", json=payload, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["predicted_emission_kg"] > 0
    assert 0 <= body["confidence"] <= 100


def test_model_metrics_endpoint(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = client.get("/api/predict/metrics", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "random_forest" in body
    assert "xgboost" in body
