from datetime import datetime
from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io

from app.core.security import get_current_user
from app.database.db import cloud_metrics_collection
from app.ml.carbon_engine import calculate_carbon, green_score, REGION_CARBON_FACTORS

router = APIRouter(prefix="/api/carbon", tags=["Carbon Engine"])


class CarbonCalcRequest(BaseModel):
    energy_kwh: float
    region: str = "ap-south-1"


@router.post("/calculate")
def calculate(payload: CarbonCalcRequest, user: dict = Depends(get_current_user)):
    emission = calculate_carbon(payload.energy_kwh, payload.region)
    return {
        "energy_kwh": payload.energy_kwh,
        "region": payload.region,
        "carbon_factor": REGION_CARBON_FACTORS.get(payload.region, 0.82),
        "carbon_emission_kg": emission,
    }


@router.get("/trend")
def carbon_trend(server_id: str | None = None, days: int = 30,
                  user: dict = Depends(get_current_user)):
    """Daily aggregated carbon emission trend for charting."""
    query = {"server_id": server_id} if server_id else {}
    docs = list(cloud_metrics_collection().find(query).sort("timestamp", 1))

    daily = defaultdict(float)
    for d in docs:
        ts = d["timestamp"]
        key = ts.strftime("%Y-%m-%d") if isinstance(ts, datetime) else str(ts)[:10]
        daily[key] += d["carbon_emission"]

    labeled = sorted(daily.items())[-days:]
    return {"labels": [k for k, _ in labeled], "values": [round(v, 2) for _, v in labeled]}


@router.get("/multi-cloud-comparison")
def multi_cloud_comparison(user: dict = Depends(get_current_user)):
    """
    Compares average carbon efficiency across regions present in the data,
    used for the 'AWS vs Azure vs GCP' style comparison card. Since this
    project simulates AWS CloudWatch, "providers" are represented by region
    groupings which map to real multi-cloud provider footprints in production.
    """
    docs = list(cloud_metrics_collection().find())
    by_region = defaultdict(lambda: {"energy": 0.0, "carbon": 0.0, "count": 0})
    for d in docs:
        r = d["region"]
        by_region[r]["energy"] += d["energy_consumption"]
        by_region[r]["carbon"] += d["carbon_emission"]
        by_region[r]["count"] += 1

    result = []
    for region, agg in by_region.items():
        count = max(1, agg["count"])
        result.append({
            "region": region,
            "avg_energy_kwh": round(agg["energy"] / count, 2),
            "avg_carbon_kg": round(agg["carbon"] / count, 2),
            "carbon_factor": REGION_CARBON_FACTORS.get(region, 0.82),
            "efficiency_rank": None,
        })

    result.sort(key=lambda r: r["carbon_factor"])
    for i, r in enumerate(result, start=1):
        r["efficiency_rank"] = i

    return {"comparison": result}


@router.get("/energy-trend")
def energy_trend(server_id: str | None = None, days: int = 30,
                  user: dict = Depends(get_current_user)):
    """Daily aggregated energy consumption trend for charting (kWh)."""
    query = {"server_id": server_id} if server_id else {}
    docs = list(cloud_metrics_collection().find(query).sort("timestamp", 1))

    daily = defaultdict(float)
    for d in docs:
        ts = d["timestamp"]
        key = ts.strftime("%Y-%m-%d") if isinstance(ts, datetime) else str(ts)[:10]
        daily[key] += d["energy_consumption"]

    labeled = sorted(daily.items())[-days:]
    return {"labels": [k for k, _ in labeled], "values": [round(v, 2) for _, v in labeled]}


@router.get("/provider-comparison")
def provider_comparison(user: dict = Depends(get_current_user)):
    """
    Multi-cloud comparison: AWS vs Azure vs GCP, aggregated from the
    `cloud_provider` field populated by /api/cloud/simulate (or set
    explicitly when ingesting real metrics).
    """
    docs = list(cloud_metrics_collection().find())
    by_provider = defaultdict(lambda: {"energy": 0.0, "carbon": 0.0, "count": 0, "servers": set()})

    for d in docs:
        provider = d.get("cloud_provider", "AWS")
        agg = by_provider[provider]
        agg["energy"] += d["energy_consumption"]
        agg["carbon"] += d["carbon_emission"]
        agg["count"] += 1
        agg["servers"].add(d["server_id"])

    result = []
    for provider, agg in by_provider.items():
        count = max(1, agg["count"])
        result.append({
            "provider": provider,
            "server_count": len(agg["servers"]),
            "avg_energy_kwh": round(agg["energy"] / count, 2),
            "avg_carbon_kg": round(agg["carbon"] / count, 2),
            "total_carbon_kg": round(agg["carbon"], 2),
            "efficiency_rank": None,
        })

    result.sort(key=lambda r: r["avg_carbon_kg"])
    for i, r in enumerate(result, start=1):
        r["efficiency_rank"] = i

    return {"comparison": result}


@router.get("/report/pdf")
def generate_pdf_report(server_id: str | None = None, user: dict = Depends(get_current_user)):
    """Generates a downloadable carbon footprint PDF report."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas

    query = {"server_id": server_id} if server_id else {}
    docs = list(cloud_metrics_collection().find(query).sort("timestamp", -1).limit(200))

    total_emission = sum(d["carbon_emission"] for d in docs)
    total_energy = sum(d["energy_consumption"] for d in docs)
    avg_score = (
        round(sum(green_score(d["cpu_usage"], d["memory_usage"], d["carbon_emission"],
                               d["energy_consumption"]) for d in docs) / len(docs))
        if docs else 0
    )

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 20)
    c.drawString(2 * cm, height - 2.5 * cm, "GreenAI Carbon Footprint Report")

    c.setFont("Helvetica", 11)
    c.drawString(2 * cm, height - 3.3 * cm,
                 f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    c.drawString(2 * cm, height - 3.9 * cm,
                 f"Scope: {server_id if server_id else 'All monitored servers'}")

    y = height - 5.2 * cm
    c.setFont("Helvetica-Bold", 13)
    c.drawString(2 * cm, y, "Summary")
    c.setFont("Helvetica", 11)
    lines = [
        f"Total Carbon Emission: {total_emission:.2f} kg CO2",
        f"Total Energy Consumed: {total_energy:.2f} kWh",
        f"Sustainability (Green) Score: {avg_score}/100",
        f"Records analyzed: {len(docs)}",
    ]
    for i, line in enumerate(lines):
        c.drawString(2 * cm, y - (i + 1) * 0.8 * cm, line)

    y2 = y - (len(lines) + 2) * 0.8 * cm
    c.setFont("Helvetica-Bold", 13)
    c.drawString(2 * cm, y2, "Recent Readings")
    c.setFont("Helvetica", 9)
    y3 = y2 - 0.7 * cm
    for d in docs[:20]:
        ts = d["timestamp"]
        ts_str = ts.strftime("%Y-%m-%d") if isinstance(ts, datetime) else str(ts)[:10]
        c.drawString(2 * cm, y3,
                     f"{ts_str}  {d['server_id']}  CPU {d['cpu_usage']}%  "
                     f"Energy {d['energy_consumption']} kWh  "
                     f"Carbon {d['carbon_emission']} kg")
        y3 -= 0.5 * cm
        if y3 < 2 * cm:
            c.showPage()
            y3 = height - 2 * cm

    c.showPage()
    c.save()
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=greenai_carbon_report.pdf"},
    )
