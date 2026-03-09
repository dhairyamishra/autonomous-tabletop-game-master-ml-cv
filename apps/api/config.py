"""Application configuration loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database — defaults to local SQLite; set DATABASE_URL env to a
    # postgresql+asyncpg:// string to switch back to Postgres.
    database_url: str = "sqlite+aiosqlite:///./referee.db"

    # App
    app_name: str = "WW2 Pacific Referee API"
    app_version: str = "1.0.0"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:3000"]

    # Camera
    camera_device_index: int = 0
    camera_capture_fps: int = 5

    # CV model paths
    detection_model_path: str = "models/detector.pt"
    calibration_model_path: str = "models/calibration.pt"


settings = Settings()
