"""Application configuration loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = "postgresql+asyncpg://referee:referee@localhost:5432/referee_db"
    database_url_sync: str = "postgresql+psycopg2://referee:referee@localhost:5432/referee_db"

    # App
    app_name: str = "WW2 Pacific Referee API"
    app_version: str = "1.0.0"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Security
    secret_key: str = "changeme-in-production-with-a-real-random-secret"
    token_expire_minutes: int = 60 * 24  # 24 hours

    # Camera
    camera_device_index: int = 0
    camera_capture_fps: int = 5

    # CV model paths
    detection_model_path: str = "models/detector.pt"
    calibration_model_path: str = "models/calibration.pt"


settings = Settings()
