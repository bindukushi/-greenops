from app.ml.greenops_engine import generate_recommendations


def test_empty_history_returns_no_recommendations():
    assert generate_recommendations([], "ap-south-1") == []


def test_idle_server_triggers_resource_optimization():
    history = [
        {"cpu_usage": 8, "memory_usage": 10, "energy_consumption": 50, "storage": 100}
        for _ in range(5)
    ]
    recs = generate_recommendations(history, "ap-south-1")
    categories = [r["category"] for r in recs]
    assert "Resource Optimization" in categories


def test_overloaded_server_triggers_workload_optimization():
    history = [
        {"cpu_usage": 95, "memory_usage": 92, "energy_consumption": 300, "storage": 200}
        for _ in range(5)
    ]
    recs = generate_recommendations(history, "ap-south-1")
    categories = [r["category"] for r in recs]
    assert "Workload Optimization" in categories


def test_healthy_server_returns_status_ok():
    history = [
        {"cpu_usage": 55, "memory_usage": 60, "energy_consumption": 120, "storage": 200}
        for _ in range(5)
    ]
    recs = generate_recommendations(history, "eu-north-1")
    assert any(r["category"] == "Status" for r in recs)
