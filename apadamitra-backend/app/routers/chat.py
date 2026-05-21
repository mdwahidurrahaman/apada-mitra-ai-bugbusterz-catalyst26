from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.alert import ChatMessage, Alert, UserAlert
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.weather import fetch_weather
from app.services.ml import predict_all
from app.services.mitigation import get_all_active_strategies
from app.services.alert_engine import get_severity
from app.services.chat import get_chat_response

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Fetch live weather
    weather = await fetch_weather(current_user.lat, current_user.lon)

    # Get current predictions to build mitigation context
    raw = predict_all(weather)
    severity_map = {
        disaster: get_severity(prob)
        for disaster, prob in raw.items()
    }
    active_mitigations = get_all_active_strategies(
        predictions={k: v.value if v else None for k, v in severity_map.items()},
        occupation=current_user.occupation.value,
    )

    # Alert summary string
    alert_summary = ", ".join(
        f"{d} ({s.value})"
        for d, s in severity_map.items()
        if s is not None
    ) or "None"

    # Fetch last 10 messages for conversation continuity
    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.asc())
        .limit(10)
        .all()
    )

    response_text = await get_chat_response(
        user_message=request.message,
        user_name=current_user.name,
        occupation=current_user.occupation.value,
        weather=weather,
        active_alerts=alert_summary,
        active_mitigations=active_mitigations,
        chat_history=[{"role": m.role, "content": m.content} for m in history],
    )

    db.add(ChatMessage(
        user_id=current_user.id, role="user", content=request.message
    ))
    db.add(ChatMessage(
        user_id=current_user.id, role="assistant", content=response_text
    ))
    db.commit()

    return ChatResponse(response=response_text)