"""
ApadaMitra AI - Main Application
FastAPI backend for disaster prediction and mitigation

Usage:
    uvicorn app.main:app --reload
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from dotenv import load_dotenv

load_dotenv()

from app.routes.predict import router as predict_router
from app.routes.mitigation import router as mitigation_router
from app.routes.voice import router as voice_router
from app.routes.sms import router as sms_router
from app.middleware.rate_limiter import RateLimitMiddleware
from app.services.gemini_service import GeminiService
from app.services.prediction_service import PredictionService
from app.services.sms_service import SmsService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def api_error_response(status_code: int, message: str, code: str, details=None):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "data": None,
            "error": {
                "code": code,
                "details": details,
            },
        },
    )


app = FastAPI(
    title="ApadaMitra AI Backend",
    description="Disaster prediction, mitigation advice, voice assistant, and SMS alerts.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "*").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

app.include_router(predict_router)
app.include_router(mitigation_router)
app.include_router(voice_router)
app.include_router(sms_router)


@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("ApadaMitra AI Backend Starting...")
    logger.info("Environment: %s", os.getenv("ENVIRONMENT", "development"))
    logger.info("Alert threshold: %s%%", os.getenv("ALERT_THRESHOLD", "70"))
    logger.info("Gemini configured: %s", os.getenv("GEMINI_API_KEY") is not None)
    logger.info("Twilio configured: %s", SmsService().is_available())
    logger.info("=" * 60)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return api_error_response(
        status_code=exc.status_code,
        message=detail,
        code="HTTP_ERROR",
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return api_error_response(
        status_code=422,
        message="Validation failed.",
        code="VALIDATION_ERROR",
        details=jsonable_encoder(exc.errors()),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", str(exc), exc_info=True)
    return api_error_response(
        status_code=500,
        message="An unexpected error occurred. Please try again later.",
        code="INTERNAL_SERVER_ERROR",
    )


@app.get("/", summary="Health check")
async def root() -> Dict[str, str]:
    return {"status": "running"}


@app.get("/health", summary="Detailed health check")
async def health_check() -> Dict[str, Any]:
    predictor = PredictionService()
    models_loaded = await run_in_threadpool(predictor._load_all_models)
    sms_service = SmsService()
    gemini_service = GeminiService()

    return {
        "status": "healthy",
        "service": "ApadaMitra AI Backend",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "dependencies": {
            "models_loaded": models_loaded,
            "sms_available": sms_service.is_available(),
            "gemini_available": gemini_service.is_available(),
            "alert_threshold": predictor.threshold,
        },
        "endpoints": {
            "prediction": "/api/predict",
            "mitigation": "/api/mitigation",
            "voice": "/api/voice-chat",
            "sms": "/api/sms-alert",
            "docs": "/docs",
        },
    }


@app.get("/api", tags=["Root"])
async def api_documentation():
    return {
        "message": "ApadaMitra AI API",
        "version": "1.0.0",
        "endpoints": {
            "health": {"GET /": "Server health check", "GET /health": "Detailed health status"},
            "prediction": {
                "POST /api/predict": "Predict disaster risk; auto-SMS on high alert when phone_number is sent",
                "GET /api/predict/health": "Prediction service health",
            },
            "mitigation": {"POST /api/mitigation": "Get mitigation advice"},
            "voice": {
                "POST /api/voice-chat": "Voice/chat assistant",
                "GET /api/voice-chat/health": "Voice service health",
            },
            "sms": {
                "POST /api/sms-alert": "Send SMS alert manually",
                "GET /api/sms-alert/health": "SMS alert service health",
            },
            "documentation": {"Swagger UI": "/docs", "ReDoc": "/redoc"},
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True,
        log_level="info",
    )
