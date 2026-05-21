from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.alert import Alert, UserAlert
from app.schemas.alert import AlertResponse, CronRunResponse
from app.services.alert_engine import run_alert_pipeline

router = APIRouter()


@router.get("/me", response_model=List[AlertResponse])
def get_my_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(UserAlert, Alert)
        .join(Alert, UserAlert.alert_id == Alert.id)
        .filter(UserAlert.user_id == current_user.id)
        .order_by(Alert.created_at.desc())
        .limit(20)
        .all()
    )
    return [
        AlertResponse(
            id=alert.id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            district=alert.district,
            probability=alert.probability,
            created_at=alert.created_at,
            sms_sent=user_alert.sms_sent,
        )
        for user_alert, alert in rows
    ]


@router.post("/trigger", response_model=CronRunResponse)
async def manual_trigger(db: Session = Depends(get_db)):
    """Manually fire the alert pipeline — for demo use."""
    count = await run_alert_pipeline(db)
    return CronRunResponse(
        message="Alert pipeline executed successfully",
        alerts_triggered=count,
    )
