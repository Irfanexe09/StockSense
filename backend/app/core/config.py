"""
StockSense — Application configuration.

Reads settings from environment variables so that secrets
are never hardcoded in source files.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "StockSense"
    debug: bool = False

    # Database
    database_url: str = (
        "postgresql://stocksense:change_me@localhost:5432/stocksense"
    )

    # CORS — origins allowed to call the API
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# Single shared instance imported throughout the app
settings = Settings()
