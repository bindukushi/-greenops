import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def auth_token():
    creds = {"name": "Monitor", "email": "monitor@example.com", "password": "MonitorPass1"}
    client.post("/api/auth/register", json=creds)
    resp = client.post("/api/auth/login", json={"email": creds["email"], "password": creds["password"]})
    return resp.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_run_daily_job_with_no_data_reports_gracefully(auth_token):
    """A fresh account with zero telemetry should get a clean message, not an error."""
    headers = auth_headers(auth_token)
    resp = client.get("/api/monitoring/scheduler/status", headers=headers)
    assert resp.status_code == 200
    assert "running" in resp.json()


def test_daily_job_full_cycle(auth_token):
    headers = auth_headers(auth_token)

    # Seed telemetry so the daily job has something to work with
    client.post("/api/cloud/simulate?days=10", headers=headers)

    resp = client.post("/api/monitoring/run-daily-job", headers=headers)
    assert resp.status_code == 200
    digest = resp.json()
    assert digest["servers_processed"] > 0
    assert "total_emission_kg" in digest
    assert "top_offender_server" in digest

    # Reports should now be listable
    reports_resp = client.get("/api/monitoring/daily-reports", headers=headers)
    assert reports_resp.status_code == 200
    assert len(reports_resp.json()["reports"]) >= 1


def test_forecast_accuracy_appears_after_second_run(auth_token):
    headers = auth_headers(auth_token)
    client.post("/api/cloud/simulate?days=5", headers=headers)

    # First run creates forecasts but no accuracy records yet (no prior forecast to score)
    client.post("/api/monitoring/run-daily-job", headers=headers)
    # Second run scores the first run's forecasts against new "actuals"
    client.post("/api/monitoring/run-daily-job", headers=headers)

    resp = client.get("/api/monitoring/forecast-accuracy", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["accuracy"]) > 0


def test_budget_get_and_update(auth_token):
    headers = auth_headers(auth_token)
    resp = client.get("/api/monitoring/budget", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["daily_limit_kg"] > 0

    update_resp = client.put("/api/monitoring/budget", json={"daily_limit_kg": 50}, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["daily_limit_kg"] == 50

    confirm_resp = client.get("/api/monitoring/budget", headers=headers)
    assert confirm_resp.json()["daily_limit_kg"] == 50


def test_budget_breach_creates_alert(auth_token):
    headers = auth_headers(auth_token)
    # Set an unreasonably low budget so today's total is guaranteed to breach it
    client.put("/api/monitoring/budget", json={"daily_limit_kg": 0.01}, headers=headers)
    client.post("/api/monitoring/run-daily-job", headers=headers)

    resp = client.get("/api/monitoring/alerts", params={"alert_type": "budget"}, headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["alerts"]) >= 1


def test_inject_anomaly_and_detect_it(auth_token):
    headers = auth_headers(auth_token)

    # Use a dedicated server with deliberately low-variance history so the
    # injected spike is unambiguously detectable, regardless of what other
    # tests may have already written into the shared test database.
    target = "ANOMALY_TEST_SERVER"
    for _ in range(10):
        client.post("/api/cloud/metrics", json={
            "server_id": target, "region": "ap-south-1",
            "cpu_usage": 45, "memory_usage": 50, "storage": 300,
            "network_traffic": 40, "energy_consumption": 120, "temperature": 24,
        }, headers=headers)

    inject_resp = client.post(
        "/api/monitoring/inject-test-anomaly", params={"server_id": target}, headers=headers
    )
    assert inject_resp.status_code == 200

    client.post("/api/monitoring/run-daily-job", headers=headers)

    resp = client.get("/api/monitoring/alerts", params={"alert_type": "anomaly"}, headers=headers)
    assert resp.status_code == 200
    alerts = resp.json()["alerts"]
    assert any(a["server_id"] == target for a in alerts)
