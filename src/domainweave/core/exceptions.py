"""Common exception hierarchy for the platform.

Design rules:
- Every application exception inherits from AppError so callers can
  catch the entire hierarchy with a single except clause.
- Each exception carries a stable, machine-readable error_code so that
  API error responses and log correlation do not depend on message strings.
- Human-readable messages must be safe to surface to callers; they must not
  contain credentials, internal stack details, or sensitive data.
"""

from __future__ import annotations


class AppError(Exception):
    """Base exception for all application-defined errors.

    Attributes:
        error_code: Stable, upper-snake-case identifier for the error
                    category (e.g. 'CONFIGURATION_ERROR').  Never changes
                    once published; used by clients and log parsers.
        message:    Human-readable description safe to surface to callers.
    """

    error_code: str = "APP_ERROR"

    def __init__(self, message: str, error_code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if error_code is not None:
            self.error_code = error_code

    def __repr__(self) -> str:
        return f"{type(self).__name__}(error_code={self.error_code!r}, message={self.message!r})"


class ConfigurationError(AppError):
    """Raised when application configuration is missing or invalid.

    Use this when a required setting is absent, a value fails validation,
    or a configuration file cannot be parsed.  Do not include the raw
    invalid value in the message if it might be a secret.
    """

    error_code: str = "CONFIGURATION_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message, error_code=self.error_code)

class DomainNotFoundError(AppError):
    """Raised when a requested domain identifier is not registered.

    Carries the requested domain_id so callers can include it in error
    responses without re-parsing the message string.
    """

    error_code: str = "DOMAIN_NOT_FOUND"

    def __init__(self, domain_id: str) -> None:
        super().__init__(
            f"Domain '{domain_id}' is not registered.",
            error_code=self.error_code,
        )
        self.domain_id = domain_id


class ModelGatewayError(AppError):
    """Raised when the Model Gateway cannot fulfil a request.

    Covers unknown profiles, provider initialisation failures, and
    normalised provider errors.  Never includes raw credentials or
    full provider stack traces in the message.
    """

    error_code: str = "MODEL_GATEWAY_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message, error_code=self.error_code)
