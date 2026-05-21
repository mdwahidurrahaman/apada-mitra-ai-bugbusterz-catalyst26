"""
Prediction Routes
API endpoints for disaster prediction and automatic high-alert SMS.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from starlette.concurrency import run_in_threadpool

from app.schemas.request_models import PredictionRequest
from app.schemas.response_models import PredictionResponse
from app.services.prediction_service import PredictionService
from app.services.sms_service import SmsService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["Prediction"],
)


def _build_alert_sms_message(result: Dict[str, Any]) -> str:
    high_alerts: List[Dict[str, Any]] = result.get("high_alerts") or []
    if not high_alerts:
        return (
            "High disaster risk detected near your location. "
            "Follow official instructions and prepare emergency supplies."
        )

    parts = [
        f"{item['disaster']} {item['probability']}%"
        for item in high_alerts
    ]
    return (
        f"High alert: {', '.join(parts)}. "
        "Follow official instructions, prepare emergency supplies, "
        "and move to a safer place if advised."
    )


def _attach_sms_alert(
    result: Dict[str, Any],
    phone_number: Optional[str],
) -> Dict[str, Any]:
    if not phone_number:
        result["sms_alert"] = {
            "sent": False,
            "message_sid": None,
            "status": "skipped",
            "error": "No phone_number provided; SMS alert was not sent.",
        }
        return result

    if not result.get("alert"):
        result["sms_alert"] = {
            "sent": False,
            "message_sid": None,
            "status": "skipped",
            "error": "No disaster probability crossed the high-alert threshold.",
        }
        return result

    sms = SmsService()
    high_alerts = result.get("high_alerts") or []
    primary = high_alerts[0] if high_alerts else {}
    location = result.get("location") or {}
    lat = location.get("lat")
    lon = location.get("lon")
    location_label = f"{lat}, {lon}" if lat is not None and lon is not None else None

    result["sms_alert"] = sms.send_alert(
        to_number=phone_number,
        disaster=primary.get("disaster") or result.get("predicted_disaster"),
        probability=primary.get("probability") or result.get("confidence"),
        location=location_label,
        message=_build_alert_sms_message(result),
    )
    return result


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict disaster risk",
    description=(
        "Predict flood, cyclone, and heatwave probability for a location. "
        "When any probability meets the alert threshold and phone_number is provided, "
        "an SMS alert is sent automatically."
    ),
)
async def predict_disaster(request: PredictionRequest) -> Dict[str, Any]:
    try:
        predictor = PredictionService()
        result = await run_in_threadpool(
            predictor.predict_disaster,
            request.lat,
            request.lon,
        )

        if result is None or result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Prediction failed. Please try again later.",
            )

        result = _attach_sms_alert(result, request.phone_number)

        if result.get("alert") and request.phone_number:
            sms_result = result.get("sms_alert") or {}
            if sms_result.get("sent"):
                logger.info(
                    "High-alert SMS sent to %s for alerts: %s",
                    request.phone_number,
                    result.get("high_alerts"),
                )
            else:
                logger.warning(
                    "High-alert SMS failed for %s: %s",
                    request.phone_number,
                    sms_result.get("error"),
                )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Prediction error: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction failed. Please try again later.",
        )


@router.get(
    "/predict/health",
    summary="Check prediction service health",
)
async def prediction_health_check() -> Dict[str, Any]:
    try:
        predictor = PredictionService()
        models_loaded = await run_in_threadpool(predictor._load_all_models)

        return {
            "status": "healthy" if models_loaded else "unhealthy",
            "models_loaded": models_loaded,
            "threshold": predictor.threshold,
            "message": (
                "Prediction service is ready"
                if models_loaded
                else "Models not found. Train and save models first."
            ),
        }
    except Exception:
        return {
            "status": "unhealthy",
            "models_loaded": False,
            "error": "Prediction service health check failed",
        }
