from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24

    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str

    # Gemini
    GEMINI_API_KEY: str

    # Scheduler
    CRON_INTERVAL_MINUTES: int = 30

    # Alert thresholds
    THRESHOLD_LOW: float = 0.20
    THRESHOLD_MEDIUM: float = 0.40
    THRESHOLD_HIGH: float = 0.70

    # Site
    SITE_URL: str = "https://apadamitra.com"

    # ML models directory (project root /models)
    MODEL_DIR: str = "../models"

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
