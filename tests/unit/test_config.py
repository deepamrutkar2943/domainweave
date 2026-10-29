"""Unit tests for core/config.py — AppSettings."""

import pytest
from pydantic import ValidationError

from domainweave.core.config import AppSettings, Environment, LogLevel


class TestAppSettingsDefaults:
    """Verify safe defaults are applied when no environment variables are set."""

    def test_default_app_name(self) -> None:
        settings = AppSettings()
        assert settings.app_name == "DomainWeave"

    def test_default_environment_is_development(self) -> None:
        settings = AppSettings()
        assert settings.environment == Environment.DEVELOPMENT

    def test_default_log_level_is_info(self) -> None:
        settings = AppSettings()
        assert settings.log_level == LogLevel.INFO

    def test_default_api_port(self) -> None:
        settings = AppSettings()
        assert settings.api_port == 8000

    def test_default_api_host(self) -> None:
        settings = AppSettings()
        assert settings.api_host == "0.0.0.0"


class TestAppSettingsOverrides:
    """Verify that explicit constructor values take precedence over defaults."""

    def test_override_environment(self) -> None:
        settings = AppSettings(environment=Environment.TESTING)
        assert settings.environment == Environment.TESTING
        assert settings.is_testing is True
        assert settings.is_development is False
        assert settings.is_production is False

    def test_override_log_level(self) -> None:
        settings = AppSettings(log_level=LogLevel.DEBUG)
        assert settings.log_level == LogLevel.DEBUG

    def test_log_level_case_insensitive_from_string(self) -> None:
        """The validator must normalise lower-case env-var strings."""
        settings = AppSettings(log_level="debug")  # type: ignore[arg-type]
        assert settings.log_level == LogLevel.DEBUG

    def test_override_app_name(self) -> None:
        settings = AppSettings(app_name="MyApp")
        assert settings.app_name == "MyApp"


class TestAppSettingsValidation:
    """Verify Pydantic validation rejects invalid values."""

    def test_invalid_port_too_low(self) -> None:
        with pytest.raises(ValidationError):
            AppSettings(api_port=0)

    def test_invalid_port_too_high(self) -> None:
        with pytest.raises(ValidationError):
            AppSettings(api_port=99999)

    def test_invalid_environment_value(self) -> None:
        with pytest.raises(ValidationError):
            AppSettings(environment="invalid_env")  # type: ignore[arg-type]

    def test_invalid_log_level_value(self) -> None:
        with pytest.raises(ValidationError):
            AppSettings(log_level="VERBOSE")  # type: ignore[arg-type]


class TestEnvironmentProperties:
    """Verify the convenience boolean properties."""

    def test_is_production_true(self) -> None:
        settings = AppSettings(environment=Environment.PRODUCTION)
        assert settings.is_production is True
        assert settings.is_development is False
        assert settings.is_testing is False

    def test_is_development_true(self) -> None:
        settings = AppSettings(environment=Environment.DEVELOPMENT)
        assert settings.is_development is True

    def test_is_testing_true(self) -> None:
        settings = AppSettings(environment=Environment.TESTING)
        assert settings.is_testing is True


class TestEnvFileLoading:
    """Verify settings load from environment variables via monkeypatching."""

    def test_env_var_overrides_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APP_NAME", "EnvApp")
        monkeypatch.setenv("LOG_LEVEL", "WARNING")
        monkeypatch.setenv("ENVIRONMENT", "production")
        # Create a fresh instance so it re-reads the patched env.
        settings = AppSettings()
        assert settings.app_name == "EnvApp"
        assert settings.log_level == LogLevel.WARNING
        assert settings.environment == Environment.PRODUCTION

