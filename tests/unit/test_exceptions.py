"""Unit tests for core/exceptions.py."""

import pytest

from domainweave.core.exceptions import AppError, ConfigurationError


class TestAppError:
    """Base exception construction and behaviour."""

    def test_is_exception_subclass(self) -> None:
        assert issubclass(AppError, Exception)

    def test_default_error_code(self) -> None:
        err = AppError("something went wrong")
        assert err.error_code == "APP_ERROR"

    def test_message_stored(self) -> None:
        err = AppError("oops")
        assert err.message == "oops"

    def test_str_is_message(self) -> None:
        err = AppError("oops")
        assert str(err) == "oops"

    def test_custom_error_code(self) -> None:
        err = AppError("oops", error_code="MY_CODE")
        assert err.error_code == "MY_CODE"

    def test_repr_contains_code_and_message(self) -> None:
        err = AppError("oops", error_code="MY_CODE")
        r = repr(err)
        assert "MY_CODE" in r
        assert "oops" in r

    def test_can_be_raised_and_caught(self) -> None:
        with pytest.raises(AppError) as exc_info:
            raise AppError("test error")
        assert exc_info.value.message == "test error"


class TestConfigurationError:
    """ConfigurationError specific behaviour."""

    def test_is_app_error_subclass(self) -> None:
        assert issubclass(ConfigurationError, AppError)

    def test_default_error_code(self) -> None:
        err = ConfigurationError("bad config")
        assert err.error_code == "CONFIGURATION_ERROR"

    def test_message_stored(self) -> None:
        err = ConfigurationError("missing API key")
        assert err.message == "missing API key"

    def test_caught_as_app_error(self) -> None:
        """ConfigurationError must be catchable as its base type."""
        with pytest.raises(AppError):
            raise ConfigurationError("bad config")

    def test_caught_as_exception(self) -> None:
        with pytest.raises(AppError):
            raise ConfigurationError("bad config")
