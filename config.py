"""
Configuration — reads from environment variables.
Copy .env.example to .env and fill in your values.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # WhatsApp Cloud API
    WHATSAPP_PHONE_NUMBER_ID: str = "1114153555115533"
    WHATSAPP_ACCESS_TOKEN: str = ""          # ← paste your permanent token here
    WEBHOOK_VERIFY_TOKEN: str = "norvelco_verify_2024"

    # Guesty API (OAuth 2.0 Client Credentials)
    GUESTY_CLIENT_ID: str = ""               # ← OAuth App Client ID
    GUESTY_CLIENT_SECRET: str = ""           # ← OAuth App Client Secret

    # Scheduler (24-hour format, America/New_York by default)
    DAILY_TASK_HOUR: int = 8                 # 8 AM
    DAILY_TASK_MINUTE: int = 0
    REVIEW_CHECK_HOUR: int = 7              # 7 AM (before cleaners start)
    REVIEW_CHECK_MINUTE: int = 30
    CELEBRATE_HOUR: int = 18               # 6 PM
    CELEBRATE_MINUTE: int = 0
    TIMEZONE: str = "America/New_York"

    # Photo requirements
    REQUIRED_PHOTOS_PER_TASK: int = 10
    REQUIRED_BEFORE_PHOTOS: int = 3  # Before-cleaning damage documentation photos

    # Damage detection (AI analysis via Claude)
    ANTHROPIC_API_KEY: str = ""          # ← Anthropic API key for vision analysis
    PROPERTY_AUTOMATION_URL: str = ""    # ← e.g. https://property-automation-production.up.railway.app
    INTERNAL_API_KEY: str = ""           # ← shared secret between norvelco_bot and property-automation

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
