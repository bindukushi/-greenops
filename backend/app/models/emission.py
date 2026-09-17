from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CloudMetricIn(BaseModel):
    server_id: str
    region: str = "ap-south-1"
    cpu_usage: float = Field(..., ge=0, le=100)
    memory_usage: float = Field(..., ge=0, le=100)
    storage: float = Field(..., ge=0, description="Storage in GB")
    network_traffic: float = Field(default=0, ge=0, description="Network I/O in GB")
    energy_consumption: float = Field(..., ge=0, description="Energy in kWh")
    temperature: float = Field(default=24.0, description="Datacenter ambient temp (C)")
    timestamp: Optional[datetime] = None


class CloudMetricOut(CloudMetricIn):
    id: str
    carbon_emission: float
    timestamp: datetime
    cloud_provider: Optional[str] = None


class PredictionRequest(BaseModel):
    server_id: str
    cpu_usage: float
    memory_usage: float
    storage: float
    network_traffic: float = 0
    energy_consumption: float
    temperature: float = 24.0
    region: str = "ap-south-1"
    horizon_days: int = Field(default=7, ge=1, le=30)
    model_name: str = Field(default="random_forest", pattern="^(random_forest|xgboost)$")


class PredictionOut(BaseModel):
    server_id: str
    model_used: str
    predicted_emission_kg: float
    confidence: float
    horizon_days: int
    generated_at: datetime


class ChatRequest(BaseModel):
    message: str
    server_id: Optional[str] = None
