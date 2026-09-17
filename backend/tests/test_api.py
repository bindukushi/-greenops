import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

TEST_USER = {
    "name": "Test User",
    "email": "test.user@example.com",
    "password": "TestPass123",
}


@pytest.fixture(scope="module")
def auth_token():
    client.post("/api/auth/register", json=TEST_USER)
    resp = client.post("/api/auth/login", json={
        "email": TEST_USER["email"], "password": TEST_USER["password"],
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_health_check():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_and_login():
    resp = client.post("/api/auth/register", json={
        "name": "Another User", "email": "another@example.com", "password": "Passw0rd!",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["user"]["email"] == "another@example.com"
    assert "access_token" in body


def test_duplicate_registration_rejected():
    resp = client.post("/api/auth/register", json=TEST_USER)
    # First registration for TEST_USER may already have happened in the
    # auth_token fixture depending on test order; either way a second
    # attempt with the same email must fail.
    client.post("/api/auth/register", json=TEST_USER)
    resp2 = client.post("/api/auth/register", json=TEST_USER)
    assert resp2.status_code == 409


def test_login_wrong_password_rejected():
    client.post("/api/auth/register", json=TEST_USER)
    resp = client.post("/api/auth/login", json={
        "email": TEST_USER["email"], "password": "wrong-password",
    })
    assert resp.status_code == 401


def test_unauthenticated_request_rejected():
    resp = client.get("/api/cloud/summary")
    assert resp.status_code == 401


def test_ingest_and_list_cloud_metric(auth_token):
    headers = auth_headers(auth_token)
    metric = {
        "server_id": "AWS999",
        "region": "ap-south-1",
        "cpu_usage": 80,
        "memory_usage": 70,
        "storage": 400,
        "network_traffic": 50,
        "energy_consumption": 300,
        "temperature": 24,
    }
    resp = client.post("/api/cloud/metrics", json=metric, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["carbon_emission"] == 246.0  # 300 * 0.82

    resp2 = client.get("/api/cloud/metrics", params={"server_id": "AWS999"}, headers=headers)
    assert resp2.status_code == 200
    assert len(resp2.json()) >= 1


def test_carbon_calculate_endpoint(auth_token):
    headers = auth_headers(auth_token)
    resp = client.post("/api/carbon/calculate",
                        json={"energy_kwh": 500, "region": "ap-south-1"},
                        headers=headers)
    assert resp.status_code == 200
    assert resp.json()["carbon_emission_kg"] == 410.0


def test_greenops_recommendations_endpoint(auth_token):
    headers = auth_headers(auth_token)
    for _ in range(3):
        client.post("/api/cloud/metrics", json={
            "server_id": "AWS998", "region": "ap-south-1",
            "cpu_usage": 10, "memory_usage": 12, "storage": 100,
            "network_traffic": 10, "energy_consumption": 60, "temperature": 22,
        }, headers=headers)

    resp = client.get("/api/greenops/recommendations",
                       params={"server_id": "AWS998"}, headers=headers)
    assert resp.status_code == 200
    categories = [r["category"] for r in resp.json()["recommendations"]]
    assert "Resource Optimization" in categories


def test_provider_comparison_endpoint(auth_token):
    headers = auth_headers(auth_token)
    client.post("/api/cloud/simulate?days=5", headers=headers)
    resp = client.get("/api/carbon/provider-comparison", headers=headers)
    assert resp.status_code == 200
    providers = [c["provider"] for c in resp.json()["comparison"]]
    assert set(providers).issubset({"AWS", "Azure", "GCP"})


def test_resource_usage_endpoint(auth_token):
    headers = auth_headers(auth_token)
    resp = client.get("/api/cloud/resource-usage", headers=headers)
    assert resp.status_code == 200
    assert "servers" in resp.json()


def test_csv_export_endpoint(auth_token):
    headers = auth_headers(auth_token)
    resp = client.get("/api/cloud/export/csv", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "server_id" in resp.text.splitlines()[0]


def test_servers_overview_endpoint(auth_token):
    headers = auth_headers(auth_token)
    client.post("/api/cloud/simulate?days=5", headers=headers)
    resp = client.get("/api/cloud/servers/overview", headers=headers)
    assert resp.status_code == 200
    servers = resp.json()["servers"]
    assert len(servers) > 0
    assert "green_score" in servers[0]
    assert "provider" in servers[0]


def test_server_detail_endpoint(auth_token):
    headers = auth_headers(auth_token)
    client.post("/api/cloud/simulate?days=5", headers=headers)
    overview = client.get("/api/cloud/servers/overview", headers=headers).json()["servers"]
    server_id = overview[0]["server_id"]

    resp = client.get(f"/api/cloud/servers/{server_id}/detail", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["server_id"] == server_id
    assert "averages" in body
    assert "latest_reading" in body


def test_server_detail_404_for_unknown_server(auth_token):
    headers = auth_headers(auth_token)
    resp = client.get("/api/cloud/servers/NOT_A_REAL_SERVER/detail", headers=headers)
    assert resp.status_code == 404


def test_live_mode_start_stop_status(auth_token):
    headers = auth_headers(auth_token)

    status_before = client.get("/api/cloud/live/status", headers=headers).json()
    assert status_before["running"] is False

    start_resp = client.post("/api/cloud/live/start?interval_seconds=2", headers=headers)
    assert start_resp.status_code == 200
    assert start_resp.json()["running"] is True

    status_running = client.get("/api/cloud/live/status", headers=headers).json()
    assert status_running["running"] is True
    assert status_running["interval_seconds"] == 2

    stop_resp = client.post("/api/cloud/live/stop", headers=headers)
    assert stop_resp.status_code == 200
    assert stop_resp.json()["running"] is False


def test_aws_integration_status_endpoint(auth_token):
    headers = auth_headers(auth_token)
    resp = client.get("/api/cloud/aws/status", headers=headers)
    assert resp.status_code == 200
    # boto3/credentials aren't configured in the test environment, so this
    # should report `configured: False` without raising an error.
    assert resp.json()["configured"] is False


def test_aws_sync_returns_400_when_not_configured(auth_token):
    headers = auth_headers(auth_token)
    resp = client.post(
        "/api/cloud/aws/sync?instance_ids=i-0123456789abcdef0", headers=headers
    )
    assert resp.status_code == 400


def test_chat_ask_endpoint(auth_token):
    headers = auth_headers(auth_token)
    resp = client.post("/api/chat/ask",
                        json={"message": "why is my carbon emission increasing?"},
                        headers=headers)
    assert resp.status_code == 200
    assert "answer" in resp.json()
