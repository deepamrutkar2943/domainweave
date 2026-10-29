"""Tests for the new exception types added in Milestone 2."""

import pytest

from domainweave.core.exceptions import (
    AppError,
    ConfigurationError,
    DomainNotFoundError,
    ModelGatewayError,
)


class TestDomainNotFoundError:
    def test_carries_domain_id(self) -> None:
        err = DomainNotFoundError("my_domain")
        assert err.domain_id == "my_domain"

    def test_error_code(self) -> None:
        assert DomainNotFoundError("x").error_code == "DOMAIN_NOT_FOUND"

    def test_message_contains_domain_id(self) -> None:
        err = DomainNotFoundError("hr_support")
        assert "hr_support" in err.message

    def test_is_domainweave_error(self) -> None:
        with pytest.raises(AppError):
            raise DomainNotFoundError("x")


class TestModelGatewayError:
    def test_error_code(self) -> None:
        assert ModelGatewayError("msg").error_code == "MODEL_GATEWAY_ERROR"

    def test_message_stored(self) -> None:
        err = ModelGatewayError("provider failed")
        assert err.message == "provider failed"

    def test_is_domainweave_error(self) -> None:
        with pytest.raises(AppError):
            raise ModelGatewayError("x")

    def test_not_configuration_error(self) -> None:
        """ModelGatewayError must NOT be caught as ConfigurationError."""
        with pytest.raises(ModelGatewayError):
            try:
                raise ModelGatewayError("x")
            except ConfigurationError:
                pass  # should NOT reach here
