"""
Admin Routes
Operational dashboard endpoints.
"""

from fastapi import APIRouter, Depends
from starlette.concurrency import run_in_threadpool
from typing import Dict, Any

from app.dependencies import require_admin
from app.services.database_service import DatabaseService
from app.services.gemini_service import GeminiService
from app.services.prediction_service import PredictionService
from app.services.sms_service import SmsService


router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"]
)


@router.get(
    "/dashboard",
    summary="Admin dashboard",
    description="Get operational counts and service status"
)
async def admin_dashboard(
    current_user: Dict[str, Any] = Depends(require_admin)
) -> Dict[str, Any]:
    database = DatabaseService()
    mongo_configured = database.is_configured()
    mongo_connected = (
        await run_in_threadpool(database.ping)
        if mongo_configured
        else False
    )

    users_count = 0
    sms_users_count = 0
    alerts_count = 0

    if mongo_connected:
        db = database.get_database()
        users_count = await run_in_threadpool(
            db["users"].count_documents,
            {}
        )
        sms_users_count = await run_in_threadpool(
            db["users"].count_documents,
            {"enable_sms_alerts": True}
        )
        alerts_count = await run_in_threadpool(
            db["alerts"].count_documents,
            {}
        )

    predictor = PredictionService()
    models_loaded = await run_in_threadpool(predictor._load_all_models)
    sms_service = SmsService()
    gemini_service = GeminiService()

    return {
        "users": {
            "total": users_count,
            "sms_enabled": sms_users_count
        },
        "alerts": {
            "total": alerts_count
        },
        "services": {
            "mongo_configured": mongo_configured,
            "mongo_connected": mongo_connected,
            "models_loaded": models_loaded,
            "sms_available": sms_service.is_available(),
            "gemini_available": gemini_service.is_available()
        }
    }
