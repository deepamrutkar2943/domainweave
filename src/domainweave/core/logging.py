"""Centralized logging configuration for DomainWeave.

Rules enforced here:
- configure_logging() is idempotent: calling it multiple times does NOT add
  duplicate handlers to the root logger.
- All application loggers inherit from the "domainweave" root logger so that
  a single log-level change affects the whole application.
- Timestamps are included in every record.
- Credentials, secrets, and full request/response bodies must never be passed
  to any logger; this module does not attempt to scrub them after the fact.
"""

import logging
import sys

_LOGGER_NAME = "domainweave"
_configured = False  # module-level guard against duplicate configuration


def configure_logging(level: str = "INFO") -> None:
    """Configure application-wide logging.

    This function is idempotent.  It must be called exactly once at
    application startup, before any loggers are used.  Subsequent calls
    are silently ignored.

    Args:
        level: A valid Python log-level name ('DEBUG', 'INFO', 'WARNING',
               'ERROR', 'CRITICAL').  Case-insensitive.
    """
    global _configured
    if _configured:
        return

    numeric_level = logging.getLevelName(level.upper())
    if not isinstance(numeric_level, int):
        # Fall back safely rather than crashing on a misconfigured env var.
        numeric_level = logging.INFO

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(numeric_level)

    app_logger = logging.getLogger(_LOGGER_NAME)
    # Guard: only add the handler if none exist yet (extra safety for test reloads).
    if not app_logger.handlers:
        app_logger.addHandler(handler)

    app_logger.setLevel(numeric_level)
    # Prevent log records from bubbling up to the root logger and being
    # printed a second time if the root logger has its own handlers.
    app_logger.propagate = False

    _configured = True


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a child logger scoped under the 'domainweave' namespace.

    Args:
        name: Dotted sub-name appended to 'domainweave', e.g. 'api.health'.
              Pass None or an empty string to get the root app logger.

    Returns:
        A :class:`logging.Logger` instance.
    """
    if name:
        return logging.getLogger(f"{_LOGGER_NAME}.{name}")
    return logging.getLogger(_LOGGER_NAME)
