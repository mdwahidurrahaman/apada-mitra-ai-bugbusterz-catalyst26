"""
Services package initialization.

Keep this module lightweight so importing one service does not eagerly load
optional integrations such as weather APIs, Twilio, Gemini, or MongoDB.
"""

__all__ = [
    "AuthService",
    "BackgroundAlertService",
    "DatabaseService",
    "GeminiService",
    "MitigationService",
    "PredictionService",
    "SmsService",
    "UserService",
    "VoiceService",
    "WeatherService"
]
