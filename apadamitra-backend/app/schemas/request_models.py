"""
Request Models (Pydantic Schemas)
Defines the structure of incoming API requests
with validation and automatic documentation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from enum import Enum


# ============================================================================
# ENUMS for validation
# ============================================================================

class UserTypeEnum(str, Enum):
    """Valid user types for mitigation advice"""
    FARMER = "farmer"
    STUDENT = "student"
    ELDERLY = "elderly"
    WORKER = "worker"
    INDUSTRY = "industry"


class DisasterTypeEnum(str, Enum):
    """Valid disaster types"""
    FLOOD = "flood"
    CYCLONE = "cyclone"
    HEATWAVE = "heatwave"


# ============================================================================
# AUTH REQUESTS
# ============================================================================

class RegisterRequest(BaseModel):
    """
    Request model for user registration

    Fields:
        name: User's full name
        email: Unique email address
        password: Password with at least 8 characters
        phone: Optional phone number for alerts
        user_type: Optional user type for personalized advice
        location: Optional location name
        lat/lon: Optional saved coordinates
        enable_sms_alerts: Whether SMS alerts should be enabled
    """
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="User's full name",
        example="Debjyoti Saha"
    )
    email: str = Field(
        ...,
        min_length=5,
        max_length=120,
        description="Unique email address",
        example="debjyoti@example.com"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password with at least 8 characters",
        example="StrongPass123"
    )
    phone: Optional[str] = Field(
        None,
        min_length=8,
        max_length=20,
        pattern=r"^\+[1-9]\d{7,14}$",
        description="Phone number in E.164 format",
        example="+919876543210"
    )
    user_type: Optional[UserTypeEnum] = Field(
        None,
        description="Type of user for personalized advice",
        example="farmer"
    )
    location: Optional[str] = Field(
        None,
        max_length=100,
        description="User location name",
        example="Malda"
    )
    lat: Optional[float] = Field(
        None,
        ge=-90,
        le=90,
        description="Saved latitude",
        example=25.61
    )
    lon: Optional[float] = Field(
        None,
        ge=-180,
        le=180,
        description="Saved longitude",
        example=88.12
    )
    enable_sms_alerts: bool = Field(
        False,
        description="Whether the user wants SMS alerts",
        example=True
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Debjyoti Saha",
                "email": "debjyoti@example.com",
                "password": "StrongPass123",
                "phone": "+919876543210",
                "user_type": "farmer",
                "location": "Malda",
                "lat": 25.61,
                "lon": 88.12,
                "enable_sms_alerts": True
            }
        }


class LoginRequest(BaseModel):
    """
    Request model for user login

    Fields:
        email: Registered email address
        password: Account password
    """
    email: str = Field(
        ...,
        min_length=5,
        max_length=120,
        description="Registered email address",
        example="debjyoti@example.com"
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Account password",
        example="StrongPass123"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "email": "debjyoti@example.com",
                "password": "StrongPass123"
            }
        }


# ============================================================================
# PREDICTION REQUEST
# ============================================================================

class PredictionRequest(BaseModel):
    """
    Request model for disaster prediction API
    
    Fields:
        lat: Latitude coordinate (e.g., 25.61)
        lon: Longitude coordinate (e.g., 88.12)
    
    Example:
        {
            "lat": 25.61,
            "lon": 88.12
        }
    """
    lat: float = Field(
        ..., 
        description="Latitude coordinate",
        ge=-90, 
        le=90,
        example=25.61
    )
    lon: float = Field(
        ..., 
        description="Longitude coordinate",
        ge=-180, 
        le=180,
        example=88.12
    )
    send_sms_alert: bool = Field(
        False,
        description="Send an SMS alert if the prediction crosses the alert threshold",
        example=False
    )
    alert_phone_number: Optional[str] = Field(
        None,
        min_length=8,
        max_length=20,
        pattern=r"^\+[1-9]\d{7,14}$",
        description="Recipient phone number in E.164 format for SMS alerts",
        example="+919876543210"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "lat": 25.61,
                "lon": 88.12,
                "send_sms_alert": False,
                "alert_phone_number": "+919876543210"
            }
        }


# ============================================================================
# MITIGATION REQUEST
# ============================================================================

class MitigationRequest(BaseModel):
    """
    Request model for mitigation advice API
    
    Fields:
        user_type: Type of user (farmer, student, elderly, worker, industry)
        disaster: Type of disaster (flood, cyclone, heatwave)
        probability: Disaster probability percentage (0-100)
    
    Example:
        {
            "user_type": "farmer",
            "disaster": "flood",
            "probability": 84
        }
    """
    user_type: UserTypeEnum = Field(
        ...,
        description="Type of user requesting advice",
        example="farmer"
    )
    disaster: DisasterTypeEnum = Field(
        ...,
        description="Type of disaster",
        example="flood"
    )
    probability: float = Field(
        ...,
        ge=0,
        le=100,
        description="Disaster probability percentage",
        example=84
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_type": "farmer",
                "disaster": "flood",
                "probability": 84
            }
        }


# ============================================================================
# VOICE CHAT REQUEST
# ============================================================================

class VoiceChatRequest(BaseModel):
    """
    Request model for voice assistant API
    
    Fields:
        question: User's question in text form
        user_type: Type of user (optional)
        location: User's location name (optional)
    
    Example:
        {
            "question": "Will flood happen near me?",
            "user_type": "farmer",
            "location": "Malda"
        }
    """
    question: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="User's question",
        example="Will flood happen near me?"
    )
    user_type: Optional[UserTypeEnum] = Field(
        None,
        description="Type of user (optional)"
    )
    location: Optional[str] = Field(
        None,
        max_length=100,
        description="User's location name",
        example="Malda"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Will flood happen near me?",
                "user_type": "farmer",
                "location": "Malda"
            }
        }


# ============================================================================
# SMS ALERT REQUEST
# ============================================================================

class SmsAlertRequest(BaseModel):
    """
    Request model for SMS alert API

    Fields:
        to_number: Recipient phone number in E.164 format
        message: Alert message body
        disaster: Optional disaster type
        probability: Optional disaster probability
        location: Optional human-readable location
    """
    to_number: str = Field(
        ...,
        min_length=8,
        max_length=20,
        pattern=r"^\+[1-9]\d{7,14}$",
        description="Recipient phone number in E.164 format",
        example="+919876543210"
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Alert message to send",
        example="High flood risk detected. Move to higher ground and follow local authority instructions."
    )
    disaster: Optional[DisasterTypeEnum] = Field(
        None,
        description="Disaster type related to the alert",
        example="flood"
    )
    probability: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Disaster probability percentage",
        example=84
    )
    location: Optional[str] = Field(
        None,
        max_length=100,
        description="Location name for the alert",
        example="Malda"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "to_number": "+919876543210",
                "message": "High flood risk detected. Move to higher ground and follow local authority instructions.",
                "disaster": "flood",
                "probability": 84,
                "location": "Malda"
            }
        }
