"""
core/config.py — Application-wide settings via Pydantic BaseSettings
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "ShiftGlass Pro"
    VERSION: str = "1.0.0"
    WORK_DAYS_PER_MONTH: int = 26       # Standard for PKR salary calculation
    REGULAR_DAY_HOURS: float = 8.0
    FRIDAY_HOURS: float = 7.0
    CURRENCY: str = "PKR"

    class Config:
        env_file = ".env"


settings = Settings()
