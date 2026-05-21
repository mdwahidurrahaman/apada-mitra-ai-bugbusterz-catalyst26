from pydantic import BaseModel
from datetime import datetime
from app.models.alert import AlertType, Severity


class AlertResponse(BaseModel):
    id: int
    alert_type: AlertType
    severity: Severity
    district: str
    probability: float
    created_at: datetime
    sms_sent: bool

    model_config = {"from_attributes": True}


class CronRunResponse(BaseModel):
    message: str
    alerts_triggered: int
