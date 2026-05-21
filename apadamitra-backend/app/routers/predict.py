import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.alert import AlertType
from app.schemas.predict import PredictionResponse, DisasterPrediction
from app.services.weather import fetch_weather, reverse_geocode
from app.services.ml import predict_all
from app.services.mitigation import get_strategies
from app.services.alert_engine import get_severity

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/current", response_model=PredictionResponse)
async def get_current_prediction(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns live disaster predictions for the authenticated user's location,
    with occupation-specific mitigation strategies for any active alerts.
    """
    weather = await fetch_weather(current_user.lat, current_user.lon)
    district = await reverse_geocode(current_user.lat, current_user.lon)
    raw = predict_all(weather)

    predictions = []
    has_active_alerts = False

    for disaster_type, probability in raw.items():
        severity = get_severity(probability)
        is_alert = severity is not None

        if is_alert:
            has_active_alerts = True

        strategies = (
            get_strategies(
                alert_type=disaster_type,
                severity=severity.value,
                occupation=current_user.occupation.value,
            )
            if is_alert else []
        )

        predictions.append(DisasterPrediction(
            disaster_type=AlertType(disaster_type),
            probability=probability,
            severity=severity,
            is_alert=is_alert,
            mitigation_strategies=strategies,
        ))

    # Active alerts first, then sorted by probability descending
    predictions.sort(key=lambda x: (-int(x.is_alert), -x.probability))

    logger.info(
        f"[PREDICT] {current_user.name} ({current_user.occupation.value}) | "
        f"{district} | alerts={'YES' if has_active_alerts else 'NO'}"
    )

    return PredictionResponse(
        user=current_user.name,
        occupation=current_user.occupation.value,
        district=district,
        weather=weather,
        predictions=predictions,
        has_active_alerts=has_active_alerts,
    )