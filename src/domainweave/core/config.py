"""Application settings for DomainWeave.

Settings are loaded from environment variables and an optional .env file.
All values have safe defaults so the application can start without a .env
file in local development. Secrets must never be committed to version control.
"""

from enum import Enum

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Deployment environment identifiers."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Allowed log level names (case-insensitive in env vars)."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AppSettings(BaseSettings):
    """Top-level application settings.

    Every field maps to an environment variable of the same name (upper-cased).
    A local .env file is loaded automatically when present; it never overrides
    real environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=False,
    )

    # --- Identity ---
    app_name: str = Field(default="DomainWeave", description="Human-readable application name.")
    app_version: str = Field(default="0.1.0", description="Application version string.")

    # --- Runtime environment ---
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Deployment environment. Controls behaviour differences between dev/test/prod.",
    )

    # --- Logging ---
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Minimum log level emitted by the application logger.",
    )

    # --- API ---
    api_host: str = Field(default="0.0.0.0", description="Host address the API server binds to.")
    api_port: int = Field(default=8000, ge=1, le=65535, description="Port the API server listens on.")

    # --- Domain Registry ---
    domains_config_dir: str = Field(
        default="configs/domains",
        description="Directory containing domain YAML configuration files.",
    )

    # --- Model Gateway ---
    model_provider: str = Field(
        default="openai",
        description="Active model provider identifier. Supported: 'openai', 'nvidia_nim'.",
    )
    openai_api_key: str = Field(
        default="",
        description="API key for the OpenAI provider. Required when model_provider='openai'.",
    )
    # NVIDIA NIM uses OpenAI-compatible endpoints; only the base_url differs.
    nvidia_nim_api_key: str = Field(
        default="",
        description="API key for NVIDIA NIM. Required when model_provider='nvidia_nim'.",
    )
    nvidia_nim_base_url: str = Field(
        default="https://integrate.api.nvidia.com/v1",
        description="Base URL for the NVIDIA NIM OpenAI-compatible endpoint.",
    )

    @field_validator("log_level", mode="before")
    @classmethod
    def normalise_log_level(cls, value: object) -> str:
        """Accept log level strings in any case (e.g. 'debug', 'INFO')."""
        if isinstance(value, str):
            return value.upper()
        return value  # type: ignore[return-value]

    @field_validator("model_provider", mode="before")
    @classmethod
    def normalise_provider(cls, value: object) -> str:
        """Normalise the provider name to lower-case."""
        if isinstance(value, str):
            return value.lower()
        return value  # type: ignore[return-value]

    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        return self.environment == Environment.TESTING

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION


def get_settings() -> AppSettings:
    """Return a fully validated AppSettings instance.

    Callers should treat this as a singleton in production code.  Tests may
    create additional instances directly with keyword arguments to override
    individual fields.
    """
    return AppSettings()

