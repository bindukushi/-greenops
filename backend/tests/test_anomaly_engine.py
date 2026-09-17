from datetime import datetime
from app.ml.anomaly_engine import detect_anomalies


def _reading(carbon, ts=None):
    return {"carbon_emission": carbon, "timestamp": ts or datetime.utcnow()}


def test_no_anomaly_in_stable_readings():
    readings = [_reading(100 + (i % 3) - 1) for i in range(10)]  # gentle, realistic variance
    result = detect_anomalies({"AWS001": readings})
    assert result == []


def test_detects_spike_anomaly():
    # 10 stable readings around 100, then a fresh spike to 500 at index 0 (most recent)
    history = [_reading(100 + (i % 3)) for i in range(10)]
    readings = [_reading(500)] + history
    result = detect_anomalies({"AWS001": readings})
    assert len(result) == 1
    assert result[0]["direction"] == "spike"
    assert result[0]["server_id"] == "AWS001"


def test_detects_drop_anomaly():
    history = [_reading(100 + (i % 3)) for i in range(10)]
    readings = [_reading(2)] + history
    result = detect_anomalies({"AWS001": readings})
    assert len(result) == 1
    assert result[0]["direction"] == "drop"


def test_insufficient_history_skips_server():
    readings = [_reading(100), _reading(200)]  # too few readings
    result = detect_anomalies({"AWS001": readings})
    assert result == []


def test_detects_spike_against_perfectly_uniform_baseline():
    """
    Zero-variance history (e.g. a freshly provisioned, very stable server)
    must not silently swallow a genuine spike due to division-by-zero
    avoidance — the floor-based fallback should still catch it.
    """
    history = [_reading(100) for _ in range(10)]
    readings = [_reading(800)] + history
    result = detect_anomalies({"AWS001": readings})
    assert len(result) == 1
    assert result[0]["direction"] == "spike"
