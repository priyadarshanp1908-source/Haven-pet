"""
Haven Pet — Core configuration.
Loads all settings from environment variables / .env file.
"""

from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import Optional

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BACKEND_DIR.as_posix()}/haven_pet.db"

    # JWT
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AI
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # CORS
    FRONTEND_URL: str = "http://localhost:5173"

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # Email (stub)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@havenpet.com"

    # Upload directory
    UPLOAD_DIR: str = str(BACKEND_DIR / "uploads")

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def normalize_sqlite_url(cls, v: str) -> str:
        if v.startswith("sqlite+aiosqlite:///./"):
            db_name = v.split("sqlite+aiosqlite:///./")[-1]
            return f"sqlite+aiosqlite:///{BACKEND_DIR.as_posix()}/{db_name}"
        return v

    @field_validator("UPLOAD_DIR", mode="after")
    @classmethod
    def normalize_upload_dir(cls, v: str) -> str:
        if not Path(v).is_absolute():
            return str(BACKEND_DIR / v)
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
