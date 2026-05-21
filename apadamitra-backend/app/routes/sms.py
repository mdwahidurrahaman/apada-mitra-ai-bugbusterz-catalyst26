"""
SMS Alert Routes
API endpoints for sending disaster alerts through Twilio.
"""

from fastapi import APIRouter, HTTPException, status
from starlette.concurrency import run_in_threadpool
from typing import Dict, Any

from app.schemas.request_models import SmsAlertRequest
from app.schemas.response_models import SmsAlertResponse
from app.services.sms_service import SmsService


router = APIRouter(
    prefix="/api",
    tags=["SMS Alerts"]
)


@router.post(
    "/sms-alert",
    response_model=SmsAlertResponse,
    summary="Send SMS alert",
    description="Send a disaster alert SMS through Twilio",
    response_description="SMS sending result with Twilio message SID"
)
async def send_sms_alert(request: SmsAlertRequest) -> Dict[str, Any]:
    """
    POST /api/sms-alert

    Sends an SMS alert using Twilio credentials configured in environment
    variables.
    """
    try:
        sms = SmsService()
        result = await run_in_threadpool(
            sms.send_alert,
            to_number=request.to_number,
            message=request.message,
            disaster=request.disaster.value if request.disaster else None,
            probability=request.probability,
            location=request.location
        )

        if not result["sent"]:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=result["error"] or "SMS alert failed"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SMS alert failed. Please try again later."
        )


@router.get(
    "/sms-alert/health",
    summary="Check SMS alert service health",
    description="Check whether Twilio SMS alert configuration is available"
)
async def sms_alert_health_check() -> Dict[str, Any]:
    sms = SmsService()
    available = sms.is_available()

    return {
        "status": "healthy" if available else "unavailable",
        "twilio_available": available,
        "message": "SMS alert service is ready" if available else "Twilio credentials or package are missing"
    }
