from datetime import datetime

from fastapi import APIRouter, Depends

from app.models.emission import PredictionRequest, PredictionOut
from app.core.security import get_current_user
from app.database.db import predictions_collection
from app.ml.predict import predict_emission, get_model_metrics

router = APIRouter(prefix="/api/predict", tags=["Prediction"])


@router.post("/", response_model=PredictionOut)
def predict(payload: PredictionRequest, user: dict = Depends(get_current_user)):
    result = predict_emission(
        cpu_usage=payload.cpu_usage,
        memory_usage=payload.memory_usage,
        storage=payload.storage,
        network_traffic=payload.network_traffic,
        energy_consumption=payload.energy_consumption,
        temperature=payload.temperature,
        region=payload.region,
        horizon_days=payload.horizon_days,
        model_name=payload.model_name,
    )

    doc = {
        "server_id": payload.server_id,
        "model_used": result["model_used"],
        "predicted_emission_kg": result["predicted_emission_kg"],
        "confidence": result["confidence"],
        "horizon_days": payload.horizon_days,
        "generated_at": datetime.utcnow(),
    }
    predictions_collection().insert_one(doc)

    return PredictionOut(**doc)


@router.get("/metrics")
def model_metrics(user: dict = Depends(get_current_user)):
    """Training performance metrics (MAE, R2, confidence) for both models."""
    return get_model_metrics()


@router.get("/history")
def prediction_history(server_id: str | None = None, limit: int = 20,
                        user: dict = Depends(get_current_user)):
    query = {"server_id": server_id} if server_id else {}
    docs = list(predictions_collection().find(query).sort("generated_at", -1).limit(limit))
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs
