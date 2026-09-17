"""
GreenAI Backend - FastAPI Application Entry Point

Run locally:
    uvicorn app.main:app --reload --port 8000

Docs available at:
    http://localhost:8000/docs   (Swagger UI)
    http://localhost:8000/redoc  (ReDoc)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database.db import is_using_mock
from app.routes import auth, cloud, carbon, prediction, greenops, chat, monitoring

app = FastAPI(
    title="GreenAI API",
    description="Cloud-Based AI System for Carbon Emission Forecasting and GreenOps Optimization",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cloud.router)
app.include_router(carbon.router)
app.include_router(prediction.router)
app.include_router(greenops.router)
app.include_router(chat.router)
app.include_router(monitoring.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "service": settings.app_name,
        "status": "online",
        "database_mode": "mongomock (in-memory demo)" if is_using_mock() else "MongoDB",
    }


@app.get("/api/health", tags=["Health"])
def health():
    return {"status": "ok"}


@app.on_event("shutdown")
def _stop_live_stream_on_shutdown():
    from app.services import live_engine
    live_engine.stop()
    from app.services import scheduler
    scheduler.shutdown()


@app.on_event("startup")
def _start_daily_scheduler():
    from app.services import scheduler
    scheduler.start()
