"""
Cloud resource monitoring routes.

Includes a `/simulate` endpoint that mimics an AWS CloudWatch GetMetricData
call: in a real deployment this would be replaced with boto3 CloudWatch
client calls, but the shape of the returned data (per-server CPU, memory,
storage, network, energy datapoints) is identical, so swapping the data
source later does not require any frontend or downstream API changes.
"""
import random
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId

from app.models.emission import CloudMetricIn, CloudMetricOut
from app.database.db import cloud_metrics_collection
from app.core.security import get_current_user
from app.core.constants import SERVER_IDS, PROVIDERS, PROVIDER_NAMES, provider_for_region as _provider_for_region
from app.ml.carbon_engine import calculate_carbon, green_score

router = APIRouter(prefix="/api/cloud", tags=["Cloud Monitoring"])

REGIONS = ["ap-south-1", "us-east-1", "eu-west-1", "eu-north-1", "us-west-2"]


def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


@router.post("/metrics", response_model=CloudMetricOut, status_code=201)
def ingest_metric(payload: CloudMetricIn, user: dict = Depends(get_current_user)):
    """Ingest a single cloud metrics reading (CPU/memory/storage/energy/etc)."""
    ts = payload.timestamp or datetime.utcnow()
    carbon = calculate_carbon(payload.energy_consumption, payload.region)

    doc = payload.model_dump()
    doc["timestamp"] = ts
    doc["carbon_emission"] = carbon
    doc["cloud_provider"] = _provider_for_region(payload.region)

    result = cloud_metrics_collection().insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize(doc)


@router.get("/metrics", response_model=list[CloudMetricOut])
def list_metrics(
    server_id: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    user: dict = Depends(get_current_user),
):
    query = {"server_id": server_id} if server_id else {}
    docs = list(
        cloud_metrics_collection().find(query).sort("timestamp", -1).limit(limit)
    )
    return [_serialize(d) for d in docs]


@router.get("/servers")
def list_servers(user: dict = Depends(get_current_user)):
    """Distinct list of servers currently reporting metrics."""
    servers = cloud_metrics_collection().distinct("server_id")
    return {"servers": servers or SERVER_IDS}


@router.get("/summary")
def dashboard_summary(user: dict = Depends(get_current_user)):
    """
    Aggregate KPIs for the dashboard cards: total emission, energy used,
    average green score, and month-over-month prediction delta.
    """
    docs = list(cloud_metrics_collection().find().sort("timestamp", -1).limit(500))
    if not docs:
        return {
            "total_emission_kg": 0, "total_energy_kwh": 0,
            "avg_green_score": 0, "server_count": 0, "trend_pct": 0,
        }

    total_emission = round(sum(d["carbon_emission"] for d in docs), 2)
    total_energy = round(sum(d["energy_consumption"] for d in docs), 2)
    scores = [
        green_score(d["cpu_usage"], d["memory_usage"], d["carbon_emission"], d["energy_consumption"])
        for d in docs
    ]
    avg_score = round(sum(scores) / len(scores))

    half = max(1, len(docs) // 2)
    recent_avg = sum(d["carbon_emission"] for d in docs[:half]) / half
    older_avg = sum(d["carbon_emission"] for d in docs[half:]) / max(1, len(docs) - half)
    trend_pct = round(((recent_avg - older_avg) / older_avg) * 100, 1) if older_avg else 0

    return {
        "total_emission_kg": total_emission,
        "total_energy_kwh": total_energy,
        "avg_green_score": avg_score,
        "server_count": len(set(d["server_id"] for d in docs)),
        "trend_pct": trend_pct,
    }


@router.post("/simulate", status_code=201)
def simulate_cloudwatch_ingest(days: int = 30, user: dict = Depends(get_current_user)):
    """
    Simulates pulling `days` worth of historical metrics from AWS CloudWatch
    for all monitored servers and stores them, so the dashboard has data to
    render immediately without waiting on real infrastructure telemetry.
    Servers are distributed across AWS / Azure / GCP so the multi-cloud
    comparison view has genuine cross-provider data to compare.
    """
    inserted = 0
    now = datetime.utcnow()
    for i, server_id in enumerate(SERVER_IDS):
        provider = PROVIDER_NAMES[i % len(PROVIDER_NAMES)]
        region = random.choice(PROVIDERS[provider]["regions"])
        base_cpu = random.uniform(25, 70)
        base_mem = random.uniform(30, 75)
        for day_offset in range(days, 0, -1):
            ts = now - timedelta(days=day_offset)
            cpu = max(1, min(100, base_cpu + random.gauss(0, 8)))
            mem = max(1, min(100, base_mem + random.gauss(0, 6)))
            storage = max(10, random.uniform(150, 900))
            network = max(0, random.gauss(60, 20))
            energy = max(5, 0.9 * cpu + 0.6 * mem + 0.02 * storage + 0.15 * network
                         + random.gauss(0, 6))
            carbon = calculate_carbon(energy, region)

            cloud_metrics_collection().insert_one({
                "server_id": server_id,
                "region": region,
                "cloud_provider": provider,
                "cpu_usage": round(cpu, 2),
                "memory_usage": round(mem, 2),
                "storage": round(storage, 2),
                "network_traffic": round(network, 2),
                "energy_consumption": round(energy, 2),
                "temperature": round(random.gauss(24, 2), 1),
                "timestamp": ts,
                "carbon_emission": carbon,
            })
            inserted += 1

    return {"message": f"Simulated {inserted} CloudWatch datapoints across "
                        f"{len(SERVER_IDS)} servers.", "inserted": inserted}


@router.get("/resource-usage")
def resource_usage_by_server(user: dict = Depends(get_current_user)):
    """Average CPU / memory / energy per server, for the dashboard's resource-usage chart."""
    docs = list(cloud_metrics_collection().find().sort("timestamp", -1).limit(2000))
    if not docs:
        return {"servers": []}

    by_server: dict[str, dict] = {}
    for d in docs:
        s = by_server.setdefault(d["server_id"], {"cpu": [], "memory": [], "energy": []})
        s["cpu"].append(d["cpu_usage"])
        s["memory"].append(d["memory_usage"])
        s["energy"].append(d["energy_consumption"])

    result = [
        {
            "server_id": sid,
            "avg_cpu": round(sum(v["cpu"]) / len(v["cpu"]), 1),
            "avg_memory": round(sum(v["memory"]) / len(v["memory"]), 1),
            "avg_energy": round(sum(v["energy"]) / len(v["energy"]), 1),
        }
        for sid, v in by_server.items()
    ]
    result.sort(key=lambda r: r["server_id"])
    return {"servers": result}


@router.get("/servers/overview")
def servers_overview(user: dict = Depends(get_current_user)):
    """
    One row per server with quick KPIs — powers the Servers list page that
    links through to each server's detail drill-down.
    """
    docs = list(cloud_metrics_collection().find().sort("timestamp", -1).limit(3000))
    if not docs:
        return {"servers": []}

    by_server: dict[str, list] = {}
    for d in docs:
        by_server.setdefault(d["server_id"], []).append(d)

    result = []
    for sid, readings in by_server.items():
        latest = readings[0]
        avg_cpu = sum(r["cpu_usage"] for r in readings) / len(readings)
        avg_mem = sum(r["memory_usage"] for r in readings) / len(readings)
        avg_energy = sum(r["energy_consumption"] for r in readings) / len(readings)
        total_carbon = sum(r["carbon_emission"] for r in readings)
        score = green_score(avg_cpu, avg_mem,
                             sum(r["carbon_emission"] for r in readings) / len(readings),
                             avg_energy)
        result.append({
            "server_id": sid,
            "provider": latest.get("cloud_provider", "AWS"),
            "region": latest.get("region"),
            "avg_cpu": round(avg_cpu, 1),
            "avg_memory": round(avg_mem, 1),
            "avg_energy_kwh": round(avg_energy, 1),
            "total_carbon_kg": round(total_carbon, 2),
            "green_score": score,
            "record_count": len(readings),
            "last_seen": latest["timestamp"],
        })

    result.sort(key=lambda r: r["server_id"])
    return {"servers": result}


@router.get("/servers/{server_id}/detail")
def server_detail(server_id: str, user: dict = Depends(get_current_user)):
    """
    Full drill-down summary for a single server: latest reading, averages,
    provider/region, sustainability score, and record count. Historical
    trend charts and GreenOps recommendations for this server reuse the
    existing /api/carbon/trend, /api/carbon/energy-trend, and
    /api/greenops/recommendations endpoints with ?server_id=<id>.
    """
    readings = list(
        cloud_metrics_collection().find({"server_id": server_id}).sort("timestamp", -1).limit(1000)
    )
    if not readings:
        raise HTTPException(status_code=404, detail=f"No telemetry found for server '{server_id}'")

    latest = readings[0]
    avg_cpu = sum(r["cpu_usage"] for r in readings) / len(readings)
    avg_mem = sum(r["memory_usage"] for r in readings) / len(readings)
    avg_storage = sum(r["storage"] for r in readings) / len(readings)
    avg_energy = sum(r["energy_consumption"] for r in readings) / len(readings)
    avg_carbon = sum(r["carbon_emission"] for r in readings) / len(readings)
    total_carbon = sum(r["carbon_emission"] for r in readings)
    score = green_score(avg_cpu, avg_mem, avg_carbon, avg_energy)

    return {
        "server_id": server_id,
        "provider": latest.get("cloud_provider", "AWS"),
        "region": latest.get("region"),
        "green_score": score,
        "record_count": len(readings),
        "first_seen": readings[-1]["timestamp"],
        "last_seen": latest["timestamp"],
        "latest_reading": _serialize(dict(latest)),
        "averages": {
            "cpu_usage": round(avg_cpu, 1),
            "memory_usage": round(avg_mem, 1),
            "storage": round(avg_storage, 1),
            "energy_consumption": round(avg_energy, 1),
            "carbon_emission": round(avg_carbon, 2),
        },
        "total_carbon_kg": round(total_carbon, 2),
    }


@router.post("/live/start")
async def start_live_mode(interval_seconds: int = 5, user: dict = Depends(get_current_user)):
    """
    Starts a background task that pushes one new simulated telemetry reading
    per server every `interval_seconds`, so the dashboard genuinely updates
    on its own — a true real-time feed, distinct from the one-shot historical
    backfill in POST /api/cloud/simulate.
    """
    from app.services import live_engine
    return live_engine.start(interval_seconds)


@router.post("/live/stop")
async def stop_live_mode(user: dict = Depends(get_current_user)):
    """Stops the live-streaming background task."""
    from app.services import live_engine
    return live_engine.stop()


@router.get("/live/status")
async def live_mode_status(user: dict = Depends(get_current_user)):
    from app.services import live_engine
    return live_engine.status()


@router.post("/aws/sync")
def sync_real_aws(instance_ids: str, region: Optional[str] = None,
                   user: dict = Depends(get_current_user)):
    """
    Pulls REAL metrics from AWS CloudWatch for the given comma-separated EC2
    instance IDs and stores them — the one endpoint in this project that
    talks to genuine infrastructure instead of simulated data.

    Requires `pip install boto3` and AWS credentials (AWS_ACCESS_KEY_ID /
    AWS_SECRET_ACCESS_KEY, optionally AWS_REGION) configured in the
    environment. See app/integrations/aws_cloudwatch.py.
    """
    from app.integrations import aws_cloudwatch

    if not aws_cloudwatch.is_configured():
        raise HTTPException(
            status_code=400,
            detail="AWS is not configured. Run `pip install boto3` and set "
                   "AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY (and optionally AWS_REGION) "
                   "in your environment, then retry.",
        )

    ids = [i.strip() for i in instance_ids.split(",") if i.strip()]
    if not ids:
        raise HTTPException(status_code=400, detail="Provide at least one EC2 instance ID.")

    readings = aws_cloudwatch.fetch_ec2_metrics(ids, region_name=region)
    inserted = 0
    for r in readings:
        energy = r["energy_consumption"] or 0
        carbon = calculate_carbon(energy, r["region"])
        cloud_metrics_collection().insert_one({
            "server_id": r["server_id"], "region": r["region"], "cloud_provider": "AWS",
            "cpu_usage": r["cpu_usage"] or 0, "memory_usage": r["memory_usage"] or 0,
            "storage": r["storage"] or 0, "network_traffic": r["network_traffic"] or 0,
            "energy_consumption": energy, "temperature": r["temperature"] or 24,
            "timestamp": r["timestamp"], "carbon_emission": carbon,
            "source": "real_aws_cloudwatch",
        })
        inserted += 1

    return {
        "message": f"Synced {inserted} REAL CloudWatch datapoints for {len(ids)} instance(s).",
        "inserted": inserted,
    }


@router.get("/aws/status")
def aws_integration_status(user: dict = Depends(get_current_user)):
    from app.integrations import aws_cloudwatch
    return {"configured": aws_cloudwatch.is_configured()}


@router.get("/export/csv")
def export_metrics_csv(server_id: Optional[str] = None, limit: int = 5000,
                        user: dict = Depends(get_current_user)):
    """Exports raw cloud metrics as a downloadable CSV file."""
    import csv
    import io
    from fastapi.responses import StreamingResponse

    query = {"server_id": server_id} if server_id else {}
    docs = list(cloud_metrics_collection().find(query).sort("timestamp", -1).limit(limit))

    buffer = io.StringIO()
    fieldnames = [
        "timestamp", "server_id", "cloud_provider", "region", "cpu_usage",
        "memory_usage", "storage", "network_traffic", "energy_consumption",
        "temperature", "carbon_emission",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for d in docs:
        row = dict(d)
        ts = row.get("timestamp")
        row["timestamp"] = ts.isoformat() if isinstance(ts, datetime) else ts
        writer.writerow(row)

    buffer.seek(0)
    filename = f"greenai_metrics_{server_id or 'all'}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
