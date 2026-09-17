
"""
Daily monitoring cycle.

This is the "advanced monitoring" layer on top of the core GreenAI
pipeline. Each run does five things:

1. Forecasts next-day emissions for every active server (Random Forest)
2. Scores the previous daily forecast against actual emissions
3. Runs anomaly detection across all servers
4. Checks today's total emission against the carbon budget
5. Stores a daily monitoring digest

Email alerts are sent only when:
- An anomaly is detected
- The carbon budget is exceeded
"""

from datetime import datetime
from statistics import mean

from app.services.email_service import send_alert_email

from app.database.db import (
    cloud_metrics_collection,
    predictions_collection,
    alerts_collection,
    daily_reports_collection,
    forecast_accuracy_collection,
    budgets_collection,
)

from app.ml.predict import predict_emission
from app.ml.anomaly_engine import detect_anomalies


DEFAULT_DAILY_BUDGET_KG = 500.0


def get_daily_budget() -> float:
    doc = budgets_collection().find_one({"scope": "global"})
    return doc["daily_limit_kg"] if doc else DEFAULT_DAILY_BUDGET_KG


def set_daily_budget(limit_kg: float) -> dict:
    budgets_collection().update_one(
        {"scope": "global"},
        {"$set": {"daily_limit_kg": limit_kg}},
        upsert=True,
    )

    return {
        "scope": "global",
        "daily_limit_kg": limit_kg,
    }


def _readings_by_server() -> dict:

    docs = list(
        cloud_metrics_collection()
        .find()
        .sort("timestamp", -1)
        .limit(3000)
    )

    by_server = {}

    for doc in docs:
        by_server.setdefault(doc["server_id"], []).append(doc)

    return by_server


def run_daily_cycle() -> dict:

    now = datetime.utcnow()

    by_server = _readings_by_server()

    if not by_server:
        return {
            "message": "No telemetry available yet. Simulate CloudWatch ingest first.",
            "servers_processed": 0,
        }

    forecasts = []
    accuracy_records = []

    # --------------------------------------------------
    # 1. FORECAST NEXT DAY EMISSION
    # --------------------------------------------------

    for server_id, readings in by_server.items():

        latest = readings[0]

        result = predict_emission(
            cpu_usage=latest["cpu_usage"],
            memory_usage=latest["memory_usage"],
            storage=latest["storage"],
            network_traffic=latest.get("network_traffic", 0),
            energy_consumption=latest["energy_consumption"],
            temperature=latest.get("temperature", 24),
            region=latest["region"],
            horizon_days=1,
            model_name="random_forest",
        )

        forecast_doc = {
            "server_id": server_id,
            "model_used": result["model_used"],
            "predicted_emission_kg": result["predicted_emission_kg"],
            "confidence": result["confidence"],
            "horizon_days": 1,
            "generated_at": now,
            "daily_job": True,
        }

        predictions_collection().insert_one(forecast_doc)

        forecasts.append(forecast_doc)

        # ----------------------------------------------
        # 2. FORECAST ACCURACY
        # ----------------------------------------------

        prior = predictions_collection().find_one(
            {
                "server_id": server_id,
                "daily_job": True,
                "generated_at": {"$lt": now},
            },
            sort=[("generated_at", -1)],
        )

        if prior:

            actual_avg = mean(
                r["carbon_emission"]
                for r in readings[:3]
            )

            predicted = prior["predicted_emission_kg"]

            error_pct = (
                abs(actual_avg - predicted)
                / max(actual_avg, 0.01)
                * 100
            )

            acc_doc = {
                "server_id": server_id,
                "predicted_emission_kg": predicted,
                "actual_emission_kg": round(actual_avg, 2),
                "error_pct": round(error_pct, 1),
                "evaluated_at": now,
            }

            forecast_accuracy_collection().insert_one(acc_doc)

            accuracy_records.append(acc_doc)

    # --------------------------------------------------
    # 3. ANOMALY DETECTION
    # --------------------------------------------------

    anomalies = detect_anomalies(by_server)

    for anomaly in anomalies:

        alert = {
            **anomaly,
            "type": "anomaly",
            "created_at": now,
            "acknowledged": False,
        }

        alerts_collection().insert_one(alert)

        # Send Email
        send_alert_email(
            subject="GreenAI Alert - Carbon Emission Anomaly",
            message=f"""
GreenAI Monitoring Alert

An anomaly has been detected.

Server ID: {anomaly.get("server_id", "Unknown")}

Message:
{anomaly.get("message", "Abnormal carbon emission detected")}

Please check the GreenAI dashboard.

Time:
{now.strftime("%Y-%m-%d %H:%M:%S")}
""",
        )

    # --------------------------------------------------
    # 4. CARBON BUDGET CHECK
    # --------------------------------------------------

    total_today = sum(
        readings[0]["carbon_emission"]
        for readings in by_server.values()
    )

    budget = get_daily_budget()

    budget_breached = total_today > budget

    if budget_breached:

        alert = {
            "type": "budget",
            "total_emission_kg": round(total_today, 2),
            "budget_kg": budget,
            "created_at": now,
            "acknowledged": False,
        }

        alerts_collection().insert_one(alert)

        # Send Email
        send_alert_email(
            subject="GreenAI Alert - Carbon Budget Exceeded",
            message=f"""
GreenAI Carbon Budget Alert

The daily carbon budget has been exceeded.

Current Emission:
{round(total_today, 2)} kg CO2

Daily Budget:
{budget} kg CO2

Exceeded By:
{round(total_today - budget, 2)} kg CO2

Please check the GreenAI Monitoring Dashboard.

Time:
{now.strftime("%Y-%m-%d %H:%M:%S")}
""",
        )

    # --------------------------------------------------
    # 5. DAILY DIGEST
    # --------------------------------------------------

    top_offender = max(
        by_server.items(),
        key=lambda item: item[1][0]["carbon_emission"],
    )

    digest = {
        "date": now.strftime("%Y-%m-%d"),
        "generated_at": now,
        "servers_processed": len(by_server),
        "total_emission_kg": round(total_today, 2),
        "budget_kg": budget,
        "budget_breached": budget_breached,
        "top_offender_server": top_offender[0],
        "top_offender_emission_kg": top_offender[1][0]["carbon_emission"],
        "anomalies_detected": len(anomalies),
        "forecasts_generated": len(forecasts),
        "accuracy_records": len(accuracy_records),
        "avg_forecast_error_pct": (
            round(
                mean(record["error_pct"] for record in accuracy_records),
                1,
            )
            if accuracy_records
            else None
        ),
    }

    daily_reports_collection().insert_one(dict(digest))

    return digest 