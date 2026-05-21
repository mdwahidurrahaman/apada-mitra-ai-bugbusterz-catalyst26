"""
ApadaMitra AI - Main Application
FastAPI backend for disaster prediction and mitigation

This is the main entry point for the backend application.
It sets up FastAPI app, routes, CORS, and middleware.

Usage:
    uvicorn app.main:app --reload

Author: ApadaMitra Team
Version: 1.0.0
"""

import os
import logging
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import routes
from app.routes.predict import router as predict_router
from app.routes.mitigation import router as mitigation_router
from app.routes.voice import router as voice_router
from app.routes.sms import router as sms_router
from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router
from app.middleware.rate_limiter import RateLimitMiddleware
from app.services.background_alert_service import BackgroundAlertService
from app.services.database_service import DatabaseService
from app.services.gemini_service import GeminiService
from app.services.prediction_service import PredictionService
from app.services.sms_service import SmsService
from app.services.user_service import UserService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
background_alert_service = BackgroundAlertService()


def api_error_response(status_code: int, message: str, code: str, details=None):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "data": None,
            "error": {
                "code": code,
                "details": details
            }
        }
    )

# ============================================================================
# CREATE FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="ApadaMitra AI Backend",
    description="""
    **Disaster Prediction and Mitigation Backend** 🌊🌀🔥
    
    This backend provides AI-powered disaster prediction and mitigation advice for:
    - **Flood Prediction**: Predict flood risk based on weather data
    - **Cyclone Prediction**: Predict cyclone risk based on atmospheric conditions
    - **Heatwave Prediction**: Predict heatwave risk based on temperature and humidity
    
    ## Features
    - Real-time weather data integration
    - ML-powered disaster prediction
    - Personalized mitigation advice
    - Voice/chat assistant
    - Fallback system for reliability
    
    ## Tech Stack
    - FastAPI for API
    - Scikit-learn for ML models
    - Google Gemini AI for intelligent responses
    - Open-Meteo for weather data
    """,
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
)

# ============================================================================
# CORS MIDDLEWARE (Cross-Origin Resource Sharing)
# ============================================================================

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

# ============================================================================
# REGISTER ROUTES
# ============================================================================

# Include all route routers
app.include_router(predict_router)
app.include_router(mitigation_router)
app.include_router(voice_router)
app.include_router(sms_router)
app.include_router(auth_router)
app.include_router(admin_router)

# ============================================================================
# LIFESPAN EVENT HANDLERS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Called when the application starts.
    Perform initialization tasks here.
    """
    logger.info("=" * 60)
    logger.info("ApadaMitra AI Backend Starting...")
    logger.info("=" * 60)
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Alert Threshold: {os.getenv('ALERT_THRESHOLD', '70')}%")
    logger.info(f"Gemini API configured: {os.getenv('GEMINI_API_KEY') is not None}")
    try:
        database = DatabaseService()
        if database.is_configured() and database.ping():
            database.ensure_indexes()
            user_service = UserService()
            admin_created = user_service.ensure_admin_user()
            seed_result = user_service.seed_demo_users()
            logger.info(
                "Startup database setup complete: admin_created=%s demo_created=%s demo_skipped=%s demo_total=%s",
                admin_created,
                seed_result["created"],
                seed_result["skipped"],
                seed_result["total"]
            )
        else:
            logger.warning("MongoDB startup setup skipped: database is not configured or unavailable")
    except Exception as e:
        logger.warning("MongoDB startup setup skipped: %s", str(e))
    background_alert_service.start()
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Called when the application shuts down.
    Perform cleanup tasks here.
    """
    logger.info("=" * 60)
    logger.info("ApadaMitra AI  Backend Shutting Down...")
    await background_alert_service.stop()
    logger.info("=" * 60)

# ============================================================================
# GLOBAL EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return api_error_response(
        status_code=exc.status_code,
        message=detail,
        code="HTTP_ERROR"
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return api_error_response(
        status_code=422,
        message="Validation failed.",
        code="VALIDATION_ERROR",
        details=jsonable_encoder(exc.errors())
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for all unhandled exceptions.
    Returns a JSON response with error details.
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return api_error_response(
        status_code=500,
        message="An unexpected error occurred. Please try again later.",
        code="INTERNAL_SERVER_ERROR"
    )

# ============================================================================
# ROOT ENDPOINTS
# ============================================================================

@app.get(
    "/",
    summary="Health check",
    description="Check if the server is running",
    response_model=Dict[str, str]
)
async def root():
    """
    GET /
    
    Health check endpoint. Returns server status.
    
    Returns:
        {"status": "running"}
    """
    return {"status": "running"}


@app.get(
    "/health",
    summary="Detailed health check",
    description="Get detailed health status of all services"
)
async def health_check() -> Dict[str, Any]:
    """
    GET /health
    
    Detailed health check endpoint. Returns status of all services.
    
    Returns:
        Dictionary with service statuses
    """
    database = DatabaseService()
    mongo_configured = database.is_configured()
    mongo_connected = (
        await run_in_threadpool(database.ping)
        if mongo_configured
        else False
    )
    predictor = PredictionService()
    models_loaded = await run_in_threadpool(predictor._load_all_models)
    sms_service = SmsService()
    gemini_service = GeminiService()

    return {
        "status": "healthy",
        "service": "ApadaMitra AI Backend",
        "version": "1.0.0",
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "dependencies": {
            "mongo_configured": mongo_configured,
            "mongo_connected": mongo_connected,
            "models_loaded": models_loaded,
            "sms_available": sms_service.is_available(),
            "gemini_available": gemini_service.is_available(),
            "background_alerts_enabled": background_alert_service.enabled
        },
        "endpoints": {
            "prediction": "/api/predict",
            "auth": "/api/auth/register",
            "admin": "/api/admin/dashboard",
            "mitigation": "/api/mitigation",
            "voice": "/api/voice-chat",
            "sms": "/api/sms-alert",
            "docs": "/docs"
        }
    }

# ============================================================================
# DOCUMENTATION HELPERS
# ============================================================================

@app.get("/api", tags=["Root"])
async def api_documentation():
    """
    GET /api
    
    API root endpoint with list of all available endpoints.
    """
    return {
        "message": "ApadaMitra AI / EarthKavach AI API",
        "version": "1.0.0",
        "endpoints": {
            "health": {
                "GET /": "Server health check",
                "GET /health": "Detailed health status"
            },
            "prediction": {
                "POST /api/predict": "Predict disaster risk",
                "GET /api/predict/health": "Prediction service health"
            },
            "auth": {
                "POST /api/auth/register": "Register user",
                "POST /api/auth/login": "Login user",
                "GET /api/auth/users": "List registered users",
                "GET /api/auth/health": "Auth database health"
            },
            "admin": {
                "GET /api/admin/dashboard": "Admin operational dashboard"
            },
            "mitigation": {
                "POST /api/mitigation": "Get mitigation advice"
            },
            "voice": {
                "POST /api/voice-chat": "Voice/chat assistant",
                "GET /api/voice-chat/health": "Voice service health"
            },
            "sms": {
                "POST /api/sms-alert": "Send SMS alert",
                "GET /api/sms-alert/health": "SMS alert service health"
            },
            "documentation": {
                "Swagger UI": "/docs",
                "ReDoc": "/redoc"
            }
        }
    }

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    """
    Main entry point for running the app directly.
    Use: python -m app.main
    """
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True,
        log_level="info"
    )
