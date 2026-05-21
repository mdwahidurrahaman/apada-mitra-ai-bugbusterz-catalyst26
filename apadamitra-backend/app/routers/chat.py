from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.alert import ChatMessage, Alert, UserAlert
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.weather import fetch_weather
from app.services.chat import get_chat_response

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    weather = await fetch_weather(current_user.lat, current_user.lon)

    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.asc())
        .limit(10)
        .all()
    )

    active_alerts = (
        db.query(Alert)
        .join(UserAlert, Alert.id == UserAlert.alert_id)
        .filter(UserAlert.user_id == current_user.id)
        .order_by(Alert.created_at.desc())
        .limit(3)
        .all()
    )
    alert_summary = (
        ", ".join(
            f"{a.alert_type.value} ({a.severity.value})" for a in active_alerts)
        or "None"
    )

    response_text = await get_chat_response(
        user_message=request.message,
        user_name=current_user.name,
        occupation=current_user.occupation.value,
        weather=weather,
        active_alerts=alert_summary,
        chat_history=[{"role": m.role, "content": m.content} for m in history],
    )

    db.add(ChatMessage(user_id=current_user.id,
           role="user", content=request.message))
    db.add(ChatMessage(user_id=current_user.id,
           role="assistant", content=response_text))
    db.commit()

    return ChatResponse(response=response_text)
