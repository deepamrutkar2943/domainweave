"""Unit tests for core/logging.py."""

import logging

from domainweave.core.logging import _LOGGER_NAME, configure_logging, get_logger


class TestConfigureLogging:
    """Verify configure_logging idempotency and handler setup."""

    def test_get_logger_returns_logger(self) -> None:
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_name_includes_namespace(self) -> None:
        logger = get_logger("api.health")
        assert logger.name == f"{_LOGGER_NAME}.api.health"

    def test_get_logger_no_name_returns_root_app_logger(self) -> None:
        logger = get_logger()
        assert logger.name == _LOGGER_NAME

    def test_get_logger_none_returns_root_app_logger(self) -> None:
        logger = get_logger(None)
        assert logger.name == _LOGGER_NAME

    def test_configure_logging_idempotent(self) -> None:
        """Calling configure_logging multiple times must not add extra handlers."""
        # configure_logging has already been called by the session fixture.
        app_logger = logging.getLogger(_LOGGER_NAME)
        handler_count_before = len(app_logger.handlers)

        configure_logging(level="DEBUG")
        configure_logging(level="INFO")

        handler_count_after = len(app_logger.handlers)
        assert handler_count_after == handler_count_before

    def test_logger_does_not_propagate_to_root(self) -> None:
        app_logger = logging.getLogger(_LOGGER_NAME)
        assert app_logger.propagate is False

    def test_child_logger_is_child_of_app_logger(self) -> None:
        child = get_logger("services.some_service")
        assert child.name.startswith(_LOGGER_NAME)
