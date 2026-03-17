from pydantic_settings import BaseSettings
from pathlib import Path


class AppSettings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./broadcaster.db"
    ENCRYPTION_KEY: str = ""
    FB_EMAIL: str = ""
    FB_PASSWORD: str = ""
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = Path(__file__).resolve().parent.parent.parent / ".env"


app_settings = AppSettings()
