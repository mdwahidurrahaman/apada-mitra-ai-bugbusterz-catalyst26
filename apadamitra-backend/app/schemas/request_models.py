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
    phone_number: Optional[str] = Field(
        None,
        min_length=8,
        max_length=20,
        pattern=r"^\+[1-9]\d{7,14}$",
        description=(
            "Recipient phone in E.164 format. When provided, the backend "
            "automatically sends an SMS if any disaster probability is a high alert."
        ),
        example="+919876543210",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "lat": 25.61,
                "lon": 88.12,
                "phone_number": "+919876543210",
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
