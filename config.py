"""
Application configuration
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""

    app_name: str = "Cortex Analyst UI"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000

    upload_dir: Path = Path("uploads")
    output_dir: Path = Path("outputs")
    static_dir: Path = Path("static")

    max_upload_size: int = 50 * 1024 * 1024

    api_timeout: int = 600000
    max_retries: int = 3
    delay_between_requests: int = 5
    polling_interval: int = 2000

    cors_origins: list[str] = ["*"]

    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_prefix = "APP_"


settings = Settings()


def create_directories():
    """Create necessary directories"""
    settings.upload_dir.mkdir(exist_ok=True)
    settings.output_dir.mkdir(exist_ok=True)
    settings.static_dir.mkdir(exist_ok=True)
