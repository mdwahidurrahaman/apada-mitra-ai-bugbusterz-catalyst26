"""
Prediction Routes
API endpoints for disaster prediction

This module contains FastAPI route handlers for disaster prediction.
Provides POST /api/predict endpoint for predicting flood, cyclone, and heatwave risk.
"""

from fastapi import APIRouter, HTTPException, status
from starlette.concurrency import run_in_threadpool
from typing import Dict, Any

from app.schemas.request_models import PredictionRequest
from app.schemas.response_models import PredictionResponse
from app.services.prediction_service import PredictionService
from app.services.sms_service import SmsService

# Create router
router = APIRouter(
    prefix="/api",
    tags=["Prediction"]
)


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict disaster risk",
    description="Predict flood, cyclone, and heatwave probability for a location",
    response_description="Disaster prediction results with probabilities and alert status"
)
async def predict_disaster(request: PredictionRequest) -> Dict[str, Any]:
    """
    POST /api/predict
    
    Predict disaster probabilities (flood, cyclone, heatwave) for a given location.
    
    The endpoint:
    1. Receives latitude and longitude
    2. Fetches live weather data (OpenWeatherMap, Open-Meteo fallback)
    3. Calculates features required by ML models
    4. Loads trained ML models and scalers
    5. Predicts probability for each disaster type
    6. Returns highest probability disaster and alert status
    
    Args:
        request: PredictionRequest containing lat and lon
        
    Returns:
        PredictionResponse with:
        - flood_probability: int (0-100)
        - cyclone_probability: int (0-100)
        - heatwave_probability: int (0-100)
        - predicted_disaster: str (highest probability disaster)
        - confidence: int (0-100, probability of predicted disaster)
        - alert: bool (True if confidence > threshold)
        - location: dict with lat/lon
        - weather_data: raw weather data used
        
    Raises:
        HTTPException: If prediction fails (500 Internal Server Error)
        
    Example Request:
        POST /api/predict
        {
            "lat": 25.61,
            "lon": 88.12
        }
    
    Example Response:
        {
            "flood_probability": 81,
            "cyclone_probability": 24,
            "heatwave_probability": 56,
            "predicted_disaster": "Flood",
            "confidence": 81,
            "alert": true,
            "location": {"lat": 25.61, "lon": 88.12},
            "weather_data": {...}
        }
    """
    try:
        # Create prediction service instance
        predictor = PredictionService()
        
        # Make prediction
        result = await run_in_threadpool(
            predictor.predict_disaster,
            request.lat,
            request.lon
        )
        
        if result is None or result.get('error'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Prediction failed. Please try again later."
            )

        if request.send_sms_alert:
            if not request.alert_phone_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="alert_phone_number is required when send_sms_alert is true."
                )

            if result.get("alert"):
                sms = SmsService()
                result["sms_alert"] = await run_in_threadpool(
                    sms.send_alert,
                    to_number=request.alert_phone_number,
                    disaster=result.get("predicted_disaster"),
                    probability=result.get("confidence"),
                    location=f"{request.lat}, {request.lon}",
                    message=(
                        "High disaster risk detected. Follow official instructions, "
                        "prepare emergency supplies, and move to a safer place if advised."
                    )
                )
            else:
                result["sms_alert"] = {
                    "sent": False,
                    "message_sid": None,
                    "status": "skipped",
                    "error": "Prediction did not cross the alert threshold."
                }
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log unexpected errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction failed. Please try again later."
        )


@router.get(
    "/predict/health",
    summary="Check prediction service health",
    description="Check if prediction service and models are available"
)
async def prediction_health_check() -> Dict[str, Any]:
    """
    GET /api/predict/health
    
    Health check endpoint for prediction service.
    Verifies that ML models are loaded and service is operational.
    
    Returns:
        Dictionary with service status
    """
    try:
        predictor = PredictionService()
        
        # Try to load models to check availability
        models_loaded = await run_in_threadpool(predictor._load_all_models)
        
        return {
            "status": "healthy" if models_loaded else "unhealthy",
            "models_loaded": models_loaded,
            "threshold": predictor.threshold,
            "message": "Prediction service is ready" if models_loaded else "Models not found. Train and save models first."
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "models_loaded": False,
            "error": "Prediction service health check failed"
        }
