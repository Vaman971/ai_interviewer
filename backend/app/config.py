"""Application configuration using Pydantic Settings.

Loads configuration from .env file or environment variables.
Provides centralized settings management for the entire application.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the AI Interviewer Platform.

    Attributes:
        app_name: Display name for the application.
        app_env: Current deployment environment.
        debug: Whether debug mode is enabled.
        secret_key: Application secret key for encryption.
        database_url: Async database connection string.
        redis_url: Redis connection URL for caching.
        openai_api_key: OpenAI API key for LLM calls.
        openai_model: OpenAI model identifier to use.
        jwt_secret: Secret key for JWT token signing.
        jwt_algorithm: Algorithm used for JWT encoding.
        jwt_expiration_minutes: JWT token expiry in minutes.
        upload_dir: Directory path for file uploads.
        max_file_size_mb: Maximum allowed upload file size.
    """

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "AI Interviewer"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    # Database
    database_url: str = "sqlite+aiosqlite:///./ai_interviewer.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LLM (OpenAI-compatible: OpenAI, Groq, Together, etc.)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    llm_base_url: str = ""  # Leave empty for OpenAI default, or set to e.g. https://api.groq.com/openai/v1

    # Speech Services
    deepgram_api_key: str = ""
    elevenlabs_api_key: str = ""

    # Avatar Services
    did_api_key: str = ""
    tavus_api_key: str = ""

    # File Storage
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 10

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440

    @property
    def upload_path(self) -> Path:
        """Return the upload directory path, creating it if absent."""
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def is_production(self) -> bool:
        """Check whether the environment is production."""
        return self.app_env == "production"

    @property
    def has_openai_key(self) -> bool:
        """Check whether a valid OpenAI API key is configured."""
        return bool(
            self.openai_api_key
            and self.openai_api_key != "your-openai-api-key"
        )


@lru_cache
def get_settings() -> Settings:
    """Return a cached application settings instance."""
    return Settings()
