"""
Configuration

Application configuration settings
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # Application
    APP_NAME: str = "NASA IoT Hub"
    APP_VERSION: str = "2.0.0"
    APP_DESCRIPTION: str = "FastAPI 3-Tier Architecture - IoT Control System"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    # Business Logic
    CONFIDENCE_THRESHOLD: float = 0.5

    # Logging
    LOG_LEVEL: str = "INFO"

    # Bluetooth (optional)
    SPEAKER_ADDRESS: Optional[str] = None
    SPEAKER_NAME: Optional[str] = None
    PHONE_ADDRESS: Optional[str] = None
    PHONE_NAME: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
