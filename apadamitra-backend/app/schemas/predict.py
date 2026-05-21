from pydantic import BaseModel
from typing import Optional
from app.models.alert import AlertType, Severity


class DisasterPrediction(BaseModel):
    disaster_type: AlertType
    probability: float
    severity: Optional[Severity]
    is_alert: bool
    mitigation_strategies: list[str]


class PredictionResponse(BaseModel):
    user: str
    occupation: str
    district: str
    weather: dict
    predictions: list[DisasterPrediction]
    has_active_alerts: bool