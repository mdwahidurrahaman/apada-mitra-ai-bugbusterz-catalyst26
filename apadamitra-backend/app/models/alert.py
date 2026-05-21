import enum
from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, JSON, Enum as SAEnum,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class AlertType(str, enum.Enum):
    cyclone = "cyclone"
    flood = "flood"
    heatwave = "heatwave"


class Severity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(SAEnum(AlertType), nullable=False)
    severity = Column(SAEnum(Severity), nullable=False)
    district = Column(String, nullable=False)
    probability = Column(Float, nullable=False)
    raw_weather_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_alerts = relationship("UserAlert", back_populates="alert")


class UserAlert(Base):
    __tablename__ = "user_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    sms_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)

    alert = relationship("Alert", back_populates="user_alerts")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
