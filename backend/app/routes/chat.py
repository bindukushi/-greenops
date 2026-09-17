from datetime import datetime

from fastapi import APIRouter, Depends

from app.models.emission import ChatRequest
from app.core.security import get_current_user
from app.database.db import cloud_metrics_collection, chat_history_collection
from app.ml.assistant import answer_question

router = APIRouter(prefix="/api/chat", tags=["AI Assistant"])


@router.post("/ask")
def ask(payload: ChatRequest, user: dict = Depends(get_current_user)):
    query = {"server_id": payload.server_id} if payload.server_id else {}
    history = list(cloud_metrics_collection().find(query).sort("timestamp", -1).limit(14))

    answer = answer_question(payload.message, history)

    chat_history_collection().insert_one({
        "user_id": str(user["_id"]),
        "server_id": payload.server_id,
        "question": payload.message,
        "answer": answer,
        "timestamp": datetime.utcnow(),
    })

    return {"question": payload.message, "answer": answer}


@router.get("/history")
def chat_history(limit: int = 20, user: dict = Depends(get_current_user)):
    docs = list(
        chat_history_collection()
        .find({"user_id": str(user["_id"])})
        .sort("timestamp", -1)
        .limit(limit)
    )
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs
