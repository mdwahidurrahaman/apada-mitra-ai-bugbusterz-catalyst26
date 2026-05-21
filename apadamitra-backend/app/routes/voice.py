"""
Voice Routes
API endpoints for voice/chat assistant

This module contains FastAPI route handlers for voice assistant interactions.
Provides POST /api/voice-chat endpoint for natural language disaster queries.
"""

from fastapi import APIRouter, HTTPException, status
from starlette.concurrency import run_in_threadpool
from typing import Dict, Any, Optional

from app.schemas.request_models import VoiceChatRequest
from app.schemas.response_models import VoiceChatResponse
from app.services.voice_service import VoiceService
from app.services.prediction_service import PredictionService

# Create router
router = APIRouter(
    prefix="/api",
    tags=["Voice Assistant"]
)


@router.post(
    "/voice-chat",
    response_model=VoiceChatResponse,
    summary="Voice/chat assistant",
    description="Process natural language questions about disasters and get intelligent responses",
    response_description="AI-generated answer with detected intent"
)
async def voice_chat(request: VoiceChatRequest) -> Dict[str, Any]:
    """
    POST /api/voice-chat
    
    Process natural language questions about disasters and get intelligent responses.
    
    The endpoint:
    1. Receives user's question, user type, and location
    2. Detects intent from question (prediction, mitigation, safety, weather, emergency)
    3. Adds context (user type, location, current prediction if available)
    4. Tries to get response from Gemini AI
    5. Falls back to hardcoded responses if AI fails (never crashes)
    6. Returns intelligent answer with detected intent
    
    Possible Intents:
        - prediction: Questions about disaster risk/prediction
        - mitigation: Questions about what to do/preparation
        - safety: Questions about safety/evacuation
        - weather: Questions about weather
        - emergency: Questions about emergency contacts/help
        - general: Other questions
        
    Args:
        request: VoiceChatRequest containing question, user_type (optional), location (optional)
        
    Returns:
        VoiceChatResponse with:
        - answer: str (intelligent response to question)
        - intent: str (detected intent from question)
        
    Example Request:
        POST /api/voice-chat
        {
            "question": "Will flood happen near me?",
            "user_type": "farmer",
            "location": "Malda"
        }
    
    Example Response:
        {
            "answer": "Heavy flood possibility nearby. Move livestock to safer locations. Current flood probability is 81%.",
            "intent": "prediction"
        }
        
    Example Request 2:
        POST /api/voice-chat
        {
            "question": "What should I do during a heatwave?",
            "user_type": "elderly"
        }
    
    Example Response 2:
        {
            "answer": "Stay indoors during peak heat (11 AM - 4 PM). Drink water frequently even if not thirsty. Take cool baths. Wear light cotton clothes. If you feel dizzy or weak, call 108 for ambulance.",
            "intent": "mitigation"
        }
    """
    try:
        # Create voice service instance
        voice = VoiceService()
        
        # Get current prediction data if location is provided
        prediction_data = None
        if request.location and request.user_type:
            try:
                # Try to get prediction for the location
                # Note: This requires location coordinates, not just name
                # For now, skip prediction data unless coordinates are provided
                pass
            except:
                pass  # Skip prediction data if unavailable
        
        # Get response
        response = await run_in_threadpool(
            voice.chat,
            question=request.question,
            user_type=request.user_type.value if request.user_type else None,
            location=request.location,
            prediction_data=prediction_data
        )
        
        if response is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate response. Please try again."
            )

        return VoiceChatResponse(**response).model_dump()
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log unexpected errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Voice chat error: {str(e)}", exc_info=True)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate voice response. Please try again."
        )


@router.get(
    "/voice-chat/health",
    summary="Check voice service health",
    description="Check if voice assistant service and AI are available"
)
async def voice_health_check() -> Dict[str, Any]:
    """
    GET /api/voice-chat/health
    
    Health check endpoint for voice assistant service.
    Verifies that Gemini AI is configured and service is operational.
    
    Returns:
        Dictionary with service status
    """
    try:
        voice = VoiceService()
        ai_available = voice.gemini_service.is_available()
        
        return {
            "status": "healthy",
            "ai_available": ai_available,
            "message": "Voice assistant is ready" if ai_available else "Voice assistant using fallback mode (AI not available)"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
