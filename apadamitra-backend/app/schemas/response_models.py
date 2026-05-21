"""
Response Models (Pydantic Schemas)
Defines the structure of API responses
with validation and automatic documentation
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# ============================================================================
# HEALTH CHECK RESPONSE
# ============================================================================

class HealthCheckResponse(BaseModel):
    """
    Response for health check endpoint (GET /)
    
    Fields:
        status: Server status ("running" or "error")
    """
    status: str = Field(
        ...,
        description="Server status",
        example="running"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "running"
            }
        }


# ============================================================================
# PREDICTION RESPONSE
# ============================================================================

class PredictionResponse(BaseModel):
    """
    Response for disaster prediction API
    
    Fields:
        flood_probability: Flood probability percentage (0-100)
        cyclone_probability: Cyclone probability percentage (0-100)
        heatwave_probability: Heatwave probability percentage (0-100)
        predicted_disaster: Name of predicted disaster with highest probability
        confidence: Confidence score (probability of predicted disaster)
        alert: Boolean indicating if alert should be triggered
        location: Location coordinates
        weather_data: Raw weather data used for prediction
    
    Example:
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
    flood_probability: int = Field(
        ...,
        ge=0,
        le=100,
        description="Flood probability percentage",
        example=81
    )
    cyclone_probability: int = Field(
        ...,
        ge=0,
        le=100,
        description="Cyclone probability percentage",
        example=24
    )
    heatwave_probability: int = Field(
        ...,
        ge=0,
        le=100,
        description="Heatwave probability percentage",
        example=56
    )
    predicted_disaster: str = Field(
        ...,
        description="Disaster with highest probability",
        example="Flood"
    )
    confidence: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confidence score of prediction",
        example=81
    )
    alert: bool = Field(
        ...,
        description="Whether any disaster crossed the high-alert threshold",
        example=True
    )
    high_alerts: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Disasters at or above the alert threshold",
        example=[{"disaster": "Flood", "probability": 81}],
    )
    alert_threshold: int = Field(
        ...,
        ge=0,
        le=100,
        description="Probability threshold used for high alerts",
        example=70,
    )
    location: Dict[str, float] = Field(
        ...,
        description="Latitude and longitude",
        example={"lat": 25.61, "lon": 88.12}
    )
    weather_data: Dict[str, Any] = Field(
        ...,
        description="Weather data used for prediction",
        example={
            "temperature": 28.5,
            "humidity": 78,
            "wind_speed": 12.3,
            "precipitation": 5.2
        }
    )
    sms_alert: Optional[Dict[str, Any]] = Field(
        None,
        description="SMS alert result when SMS sending is requested",
        example={
            "sent": True,
            "message_sid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "status": "queued",
            "error": None
        }
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "flood_probability": 81,
                "cyclone_probability": 24,
                "heatwave_probability": 56,
                "predicted_disaster": "Flood",
                "confidence": 81,
                "alert": True,
                "location": {"lat": 25.61, "lon": 88.12},
                "weather_data": {
                    "temperature": 28.5,
                    "humidity": 78,
                    "wind_speed": 12.3,
                    "precipitation": 5.2
                },
                "sms_alert": None
            }
        }


# ============================================================================
# MITIGATION RESPONSE
# ============================================================================

class MitigationResponse(BaseModel):
    """
    Response for mitigation advice API
    
    Fields:
        severity: Severity level (Low, Medium, High, Critical)
        things_to_do: List of 5 recommended actions
        things_not_to_do: List of 5 actions to avoid
        emergency_kit: List of emergency kit items
    
    Example:
        {
            "severity": "High",
            "things_to_do": [
                "Move livestock to higher ground",
                "Store enough food and water for 3 days",
                ...
            ],
            "things_not_to_do": [
                "Do not stay in low-lying areas",
                "Do not touch electrical wires",
                ...
            ],
            "emergency_kit": [
                "Flashlight with extra batteries",
                "First aid kit",
                ...
            ]
        }
    """
    severity: str = Field(
        ...,
        description="Severity level of disaster risk",
        example="High"
    )
    things_to_do: List[str] = Field(
        ...,
        min_length=5,
        max_length=5,
        description="Top 5 recommended actions",
        example=[
            "Move livestock to higher ground",
            "Store enough food and water for 3 days",
            "Secure important documents in waterproof bags",
            "Keep emergency contact numbers handy",
            "Charge mobile phones and power banks"
        ]
    )
    things_not_to_do: List[str] = Field(
        ...,
        min_length=5,
        max_length=5,
        description="Top 5 actions to avoid",
        example=[
            "Do not stay in low-lying areas",
            "Do not touch electrical wires in water",
            "Do not drink untreated water",
            "Do not walk through flowing water",
            "Do not delay evacuation if ordered"
        ]
    )
    emergency_kit: List[str] = Field(
        ...,
        min_length=5,
        max_length=5,
        description="Emergency kit items",
        example=[
            "Flashlight with extra batteries",
            "First aid kit",
            "Bottled water (3 liters per person)",
            "Non-perishable food items",
            "Raincoat and waterproof clothing"
        ]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "severity": "High",
                "things_to_do": [
                    "Move livestock to higher ground",
                    "Store enough food and water for 3 days",
                    "Secure important documents in waterproof bags",
                    "Keep emergency contact numbers handy",
                    "Charge mobile phones and power banks"
                ],
                "things_not_to_do": [
                    "Do not stay in low-lying areas",
                    "Do not touch electrical wires in water",
                    "Do not drink untreated water",
                    "Do not walk through flowing water",
                    "Do not delay evacuation if ordered"
                ],
                "emergency_kit": [
                    "Flashlight with extra batteries",
                    "First aid kit",
                    "Bottled water (3 liters per person)",
                    "Non-perishable food items",
                    "Raincoat and waterproof clothing"
                ]
            }
        }


# ============================================================================
# VOICE CHAT RESPONSE
# ============================================================================

class VoiceChatResponse(BaseModel):
    """
    Response for voice assistant API
    
    Fields:
        answer: Intelligent response to user's question
        intent: Detected intent from question
    
    Example:
        {
            "answer": "Heavy flood possibility nearby. Move livestock to safer locations.",
            "intent": "prediction"
        }
    """
    answer: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Intelligent response to user's question",
        example="Heavy flood possibility nearby. Move livestock to safer locations."
    )
    intent: str = Field(
        ...,
        description="Detected intent from question",
        example="prediction"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Heavy flood possibility nearby. Move livestock to safer locations.",
                "intent": "prediction"
            }
        }


# ============================================================================
# SMS ALERT RESPONSE
# ============================================================================

class SmsAlertResponse(BaseModel):
    """
    Response for SMS alert API

    Fields:
        sent: Whether the message was accepted by Twilio
        message_sid: Twilio message identifier when available
        status: Twilio message status or local failure state
        error: Error details when sending fails
    """
    sent: bool = Field(
        ...,
        description="Whether the SMS alert was sent or queued",
        example=True
    )
    message_sid: Optional[str] = Field(
        None,
        description="Twilio message SID",
        example="SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    )
    status: str = Field(
        ...,
        description="Message status",
        example="queued"
    )
    error: Optional[str] = Field(
        None,
        description="Error details if sending failed",
        example=None
    )

    class Config:
        json_schema_extra = {
            "example": {
                "sent": True,
                "message_sid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "status": "queued",
                "error": None
            }
        }
