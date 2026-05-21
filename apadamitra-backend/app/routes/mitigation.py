"""
Mitigation Routes
API endpoints for disaster mitigation advice

This module contains FastAPI route handlers for mitigation advice.
Provides POST /api/mitigation endpoint for getting personalized disaster response advice.
"""

from fastapi import APIRouter, HTTPException, status
from starlette.concurrency import run_in_threadpool
from typing import Dict, Any

from app.schemas.request_models import MitigationRequest
from app.schemas.response_models import MitigationResponse
from app.services.mitigation_service import MitigationService

# Create router
router = APIRouter(
    prefix="/api",
    tags=["Mitigation"]
)


@router.post(
    "/mitigation",
    response_model=MitigationResponse,
    summary="Get mitigation advice",
    description="Get personalized disaster mitigation advice based on user type, disaster type, and probability",
    response_description="Mitigation advice with things to do, things not to do, and emergency kit items"
)
async def get_mitigation_advice(request: MitigationRequest) -> Dict[str, Any]:
    """
    POST /api/mitigation
    
    Get personalized mitigation advice for a disaster scenario.
    
    The endpoint:
    1. Receives user type, disaster type, and probability
    2. Determines severity level based on probability
    3. Tries to get advice from Gemini AI (dynamic, intelligent)
    4. Falls back to hardcoded advice if AI fails (never crashes)
    5. Returns structured advice with things to do, not to do, and emergency kit
    
    Args:
        request: MitigationRequest containing user_type, disaster, and probability
        
    Returns:
        MitigationResponse with:
        - severity: str (Low, Medium, High, Critical)
        - things_to_do: List[str] (5 recommended actions)
        - things_not_to_do: List[str] (5 actions to avoid)
        - emergency_kit: List[str] (5 emergency kit items)
        
    User Types:
        - farmer: Agricultural workers
        - student: Students and school/college attendees
        - elderly: Senior citizens (60+)
        - worker: Industrial/construction workers
        - industry: Industrial/business operations
        
    Disaster Types:
        - flood: Flooding events
        - cyclone: Cyclonic storms
        - heatwave: Extreme heat events
        
    Severity Levels:
        - Low: Probability < 40%
        - Medium: Probability 40-70%
        - High: Probability 70-85%
        - Critical: Probability >= 85%
        
    Example Request:
        POST /api/mitigation
        {
            "user_type": "farmer",
            "disaster": "flood",
            "probability": 84
        }
    
    Example Response:
        {
            "severity": "High",
            "things_to_do": [
                "Move livestock to higher ground immediately",
                "Store enough food and water for 3-5 days",
                "Secure important documents in waterproof bags",
                "Raise stored grains and equipment above flood level",
                "Keep emergency contact numbers handy and charge phones"
            ],
            "things_not_to_do": [
                "Do not stay in low-lying farm areas",
                "Do not touch electrical wires in flood water",
                "Do not drink untreated flood water",
                "Do not walk or drive through flowing water",
                "Do not delay evacuation if authorities order"
            ],
            "emergency_kit": [
                "Flashlight with extra batteries",
                "First aid kit and essential medicines",
                "Bottled water (3 liters per person)",
                "Non-perishable food items",
                "Raincoat and waterproof clothing"
            ]
        }
    """
    try:
        # Create mitigation service instance
        mitigation = MitigationService()
        
        # Get advice
        advice = await run_in_threadpool(
            mitigation.get_advice,
            user_type=request.user_type.value,
            disaster=request.disaster.value,
            probability=request.probability
        )
        
        if advice is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate mitigation advice. Please try again."
            )
        
        return advice
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log unexpected errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Mitigation advice error: {str(e)}", exc_info=True)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate mitigation advice. Please try again."
        )
