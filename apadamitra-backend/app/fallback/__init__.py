"""
Fallback package initialization
Contains fallback systems when APIs fail
"""

from app.fallback.voice_fallback import VoiceFallback

__all__ = ["VoiceFallback"]