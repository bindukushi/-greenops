from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.database.db import (
    daily_reports_collection, alerts_collection, forecast_accuracy_collection,
    cloud_metrics_collection,
)
from app.ml.carbon_engine import calculate_carbon
from app.services import daily_job, scheduler

router = APIRouter(prefix="/api/monitoring", tags=["Daily Monitoring"])


class BudgetIn(BaseModel):
    daily_limit_kg: float = Field(..., gt=0)


def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


@router.post("/run-daily-job")
def trigger_daily_job(user: dict = Depends(get_current_user)):
    """
    Manually runs the full daily monitoring cycle right now: forecasts next-day
    emissions per server, scores the previous forecast's accuracy, detects
    anomalies, checks the carbon budget, and compiles a digest. The same
    cycle also runs automatically every 24 hours via the background scheduler.
    """
    return daily_job.run_daily_cycle()


@router.get("/daily-reports")
def list_daily_reports(limit: int = 14, user: dict = Depends(get_current_user)):
    docs = list(daily_reports_collection().find().sort("generated_at", -1).limit(limit))
    return {"reports": [_serialize(d) for d in docs]}


@router.get("/alerts")
def list_alerts(limit: int = 50, alert_type: Optional[str] = None,
                 user: dict = Depends(get_current_user)):
    query = {"type": alert_type} if alert_type else {}
    docs = list(alerts_collection().find(query).sort("created_at", -1).limit(limit))
    return {"alerts": [_serialize(d) for d in docs]}


@router.get("/forecast-accuracy")
def forecast_accuracy(server_id: Optional[str] = None, limit: int = 30,
                       user: dict = Depends(get_current_user)):
    query = {"server_id": server_id} if server_id else {}
    docs = list(forecast_accuracy_collection().find(query).sort("evaluated_at", -1).limit(limit))
    docs = list(reversed(docs))  # chronological order for charting
    return {"accuracy": [_serialize(d) for d in docs]}


@router.get("/budget")
def get_budget(user: dict = Depends(get_current_user)):
    return {"daily_limit_kg": daily_job.get_daily_budget()}


@router.put("/budget")
def update_budget(payload: BudgetIn, user: dict = Depends(get_current_user)):
    return daily_job.set_daily_budget(payload.daily_limit_kg)


@router.get("/scheduler/status")
def scheduler_status(user: dict = Depends(get_current_user)):
    return scheduler.status()


@router.post("/inject-test-anomaly")
def inject_test_anomaly(server_id: str, user: dict = Depends(get_current_user)):
    """
    Demo/testing utility: inserts one deliberately abnormal reading (extreme
    CPU + energy spike) for `server_id`, so the next daily job run has a
    genuine outlier to catch — useful for demonstrating the alerting
    pipeline without waiting for organic random variance to spike on its own.
    """
    existing = cloud_metrics_collection().find_one({"server_id": server_id}, sort=[("timestamp", -1)])
    region = existing["region"] if existing else "ap-south-1"
    provider = existing.get("cloud_provider", "AWS") if existing else "AWS"

    energy = 950.0  # deliberately far outside normal range
    carbon = calculate_carbon(energy, region)
    cloud_metrics_collection().insert_one({
        "server_id": server_id, "region": region, "cloud_provider": provider,
        "cpu_usage": 99.5, "memory_usage": 98.0, "storage": 900, "network_traffic": 400,
        "energy_consumption": energy, "temperature": 41.0, "timestamp": datetime.utcnow(),
        "carbon_emission": carbon, "source": "injected_test_anomaly",
    })
    return {
        "message": f"Injected an abnormal spike reading for {server_id}. "
                   "Run the daily job to see it caught by anomaly detection.",
    }
