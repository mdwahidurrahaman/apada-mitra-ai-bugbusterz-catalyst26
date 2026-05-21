"""
Routes package initialization
Contains all API route routers
"""

from app.routes.predict import router as predict_router
from app.routes.mitigation import router as mitigation_router
from app.routes.voice import router as voice_router
from app.routes.sms import router as sms_router
from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router

__all__ = [
    "predict_router",
    "mitigation_router",
    "voice_router",
    "sms_router",
    "auth_router",
    "admin_router"
]
