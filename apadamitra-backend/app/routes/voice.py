"""
Voice Routes
API endpoints for voice/chat assistant — including real-time WebSocket.
"""

import json
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status
from starlette.concurrency import run_in_threadpool

from app.schemas.request_models import VoiceChatRequest
from app.schemas.response_models import VoiceChatResponse
from app.services.voice_service import VoiceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Voice Assistant"])


# ── REST endpoint ───────────────────────────────────────────────────────────

@router.post(
    "/voice-chat",
    response_model=VoiceChatResponse,
    summary="Voice/chat assistant (REST)",
    description="Process natural language questions about disasters and get intelligent responses",
)
async def voice_chat(request: VoiceChatRequest) -> Dict[str, Any]:
    try:
        voice = VoiceService()
        response = await run_in_threadpool(
            voice.chat,
            question=request.question,
            user_type=request.user_type.value if request.user_type else None,
            location=request.location,
            prediction_data=None,
        )
        if response is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate response. Please try again.",
            )
        return VoiceChatResponse(**response).model_dump()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice chat error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate voice response. Please try again.",
        )


# ── WebSocket endpoint ──────────────────────────────────────────────────────

@router.websocket("/ws/voice-chat")
async def voice_chat_ws(websocket: WebSocket):
    """
    WebSocket endpoint for real-time streaming voice assistant.

    Protocol (JSON messages):
      Client → Server:  { "question": "...", "user_type": "farmer", "location": "Malda" }
      Server → Client:  { "type": "chunk",  "text": "..." }   (one or more)
                        { "type": "done",   "intent": "..." }
                        { "type": "error",  "text": "..." }

    NOTE: chat_stream now collects all Gemini chunks internally, parses
    the JSON response, and yields only the clean answer — so the client
    typically receives a single "chunk" message with the full answer,
    followed by "done". This guarantees no metadata or reasoning leaks
    to the frontend regardless of what Gemini returns.
    """
    await websocket.accept()
    voice = VoiceService()

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "text": "Invalid JSON"})
                continue

            question = (data.get("question") or "").strip()
            if not question:
                await websocket.send_json({"type": "error", "text": "Empty question"})
                continue

            user_type = data.get("user_type") or None
            location  = data.get("location") or None

            intent = voice._detect_intent(question)

            full_text = ""
            try:
                for chunk in voice.chat_stream(
                    question=question,
                    user_type=user_type,
                    location=location,
                ):
                    if chunk:
                        full_text += chunk
                        await websocket.send_json({"type": "chunk", "text": chunk})

            except Exception as e:
                logger.error(f"WS stream error: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "text": "Stream error. For emergencies call 112.",
                })
                continue

            await websocket.send_json({"type": "done", "intent": intent})

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)


# ── Health check ────────────────────────────────────────────────────────────

@router.get("/voice-chat/health", summary="Check voice service health")
async def voice_health_check() -> Dict[str, Any]:
    try:
        voice = VoiceService()
        ai_available = voice.gemini_service.is_available()
        return {
            "status": "healthy",
            "ai_available": ai_available,
            "websocket_endpoint": "/api/ws/voice-chat",
            "message": (
                "Voice assistant is ready"
                if ai_available
                else "Voice assistant using fallback mode (AI not available)"
            ),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}