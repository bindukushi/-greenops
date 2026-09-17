"""
Statistical anomaly detection for cloud carbon telemetry.

Uses a rolling z-score per server: computes the mean and standard deviation
of a server's recent carbon_emission history (excluding the latest reading),
then flags the latest reading as anomalous if it deviates by more than
`z_threshold` standard deviations. This is deliberately a transparent
statistical method rather than a black-box ML model — for an operational
alerting system, being able to say "this is 3.1 standard deviations above
the 14-day average" is more actionable and trustworthy than an opaque score.
"""
from statistics import mean, stdev


def detect_anomalies(readings_by_server: dict, z_threshold: float = 2.2, window: int = 14) -> list[dict]:
    """
    readings_by_server: {server_id: [readings...]}, each server's list
    sorted most-recent-first (as returned by .find().sort("timestamp", -1)).
    """
    anomalies = []
    for server_id, readings in readings_by_server.items():
        if len(readings) < 6:
            continue

        latest = readings[0]
        history = [r["carbon_emission"] for r in readings[1:window + 1]]
        if len(history) < 4:
            continue

        avg = mean(history)
        try:
            sd = stdev(history)
        except Exception:
            sd = 0

        # Guard against division by zero when history has near-zero variance
        # (e.g. a newly-provisioned server with very stable readings) —
        # use a small floor instead of skipping, so a genuine spike against
        # an otherwise rock-steady baseline still gets caught.
        sd = max(sd, avg * 0.01, 0.5)

        z = (latest["carbon_emission"] - avg) / sd
        if abs(z) >= z_threshold:
            anomalies.append({
                "server_id": server_id,
                "carbon_emission": latest["carbon_emission"],
                "expected_avg_kg": round(avg, 2),
                "z_score": round(z, 2),
                "direction": "spike" if z > 0 else "drop",
                "timestamp": latest["timestamp"],
            })

    return anomalies
