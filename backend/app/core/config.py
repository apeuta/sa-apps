"""
Konfigurasi aplikasi menggunakan Pydantic Settings.
Semua konfigurasi sensitif dibaca dari environment variables.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Konfigurasi utama aplikasi Portal SA."""

    # Aplikasi
    APP_NAME: str = "Portal SA API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/portal_sa"

    # CORS - allow all origins untuk development
    CORS_ORIGINS: List[str] = ["*"]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    # Auth
    JWT_SECRET_KEY: str = "change-this-secret-key-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    JWT_REFRESH_EXPIRE_HOURS: int = 168  # 7 hari untuk refresh token
    ALLOWED_DOMAINS: List[str] = []
    ROLE_MAPPING: str = "{}"  # JSON string: {"email@domain.com": "Admin", "*@domain.com": "SA"}

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/callback"

    # LLM Provider — Abstraction layer untuk multi-provider AI
    LLM_PROVIDER: str = "gemini"  # Provider aktif: gemini, openai, anthropic
    LLM_MODEL_NAME: str = "gemini-1.5-flash"  # Model default yang digunakan
    LLM_API_ENDPOINT: str = "https://generativelanguage.googleapis.com/v1"
    LLM_TIMEOUT_SECONDS: int = 30  # Timeout per request ke LLM
    LLM_MAX_RETRIES: int = 3  # Jumlah retry saat gagal

    # API Keys per provider
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # Google Drive
    GDRIVE_SERVICE_ACCOUNT_KEY: str = ""

    # Google Calendar
    GCAL_WEBHOOK_ENDPOINT: str = ""

    # Gmail
    GMAIL_CREDENTIALS: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton instance
settings = Settings()
