"""
Konfigurasi aplikasi menggunakan Pydantic Settings.
Semua konfigurasi sensitif dibaca dari environment variables.

Format .env untuk list fields:
- ALLOWED_DOMAINS=domain1.com,domain2.com  (comma-separated)
- CORS_ORIGINS=http://localhost:3000,http://example.com  (comma-separated)
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings


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

    # CORS - comma-separated string, di-parse jadi list
    CORS_ORIGINS: str = "*"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    # Demo Mode — bypass OAuth, login tanpa Google credentials (set False di production)
    DEMO_MODE: bool = True

    # Auth
    JWT_SECRET_KEY: str = "change-this-secret-key-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    JWT_REFRESH_EXPIRE_HOURS: int = 168  # 7 hari untuk refresh token
    ALLOWED_DOMAINS: str = ""  # Comma-separated: "domain1.com,domain2.com"
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

    @property
    def allowed_domains_list(self) -> list[str]:
        """Parse ALLOWED_DOMAINS comma-separated string menjadi list."""
        if not self.ALLOWED_DOMAINS:
            return []
        return [d.strip() for d in self.ALLOWED_DOMAINS.split(",") if d.strip()]

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS comma-separated string menjadi list."""
        if not self.CORS_ORIGINS or self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton instance
settings = Settings()
