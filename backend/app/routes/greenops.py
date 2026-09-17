from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.database.db import cloud_metrics_collection
from app.ml.greenops_engine import generate_recommendations

router = APIRouter(prefix="/api/greenops", tags=["GreenOps Optimization"])


@router.get("/recommendations")
def recommendations(server_id: str | None = None, user: dict = Depends(get_current_user)):
    query = {"server_id": server_id} if server_id else {}
    docs = list(cloud_metrics_collection().find(query).sort("timestamp", -1).limit(30))

    if server_id:
        region = docs[0]["region"] if docs else "ap-south-1"
        return {"server_id": server_id, "recommendations": generate_recommendations(docs, region)}

    # No server specified -> aggregate per-server recommendations
    by_server: dict[str, list] = {}
    for d in docs:
        by_server.setdefault(d["server_id"], []).append(d)

    all_recs = {}
    for sid, metrics in by_server.items():
        region = metrics[0]["region"]
        all_recs[sid] = generate_recommendations(metrics, region)

    return {"recommendations_by_server": all_recs}
