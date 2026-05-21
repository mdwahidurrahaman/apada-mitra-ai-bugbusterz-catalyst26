from pydantic import BaseModel, field_validator
from datetime import datetime
from app.models.user import Occupation


class UserRegisterRequest(BaseModel):
    name: str
    phone: str
    password: str
    occupation: Occupation
    lat: float
    lon: float

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not v.startswith("+"):
            raise ValueError("Phone must be E.164 format e.g. +919876543210")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()


class UserLoginRequest(BaseModel):
    phone: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    name: str
    phone: str
    occupation: Occupation
    lat: float
    lon: float
    created_at: datetime

    model_config = {"from_attributes": True}
