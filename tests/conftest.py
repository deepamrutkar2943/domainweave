"""Shared pytest fixtures for DomainWeave tests.

Fixtures here are available to all test modules without explicit import.

Design rules:
- No real LLM calls, no real database connections.
- Settings are overridden via constructor arguments or monkeypatching.
- The FastAPI TestClient is provided as a fixture so individual tests
  don't each create their own application instance.
"""

import pytest
from fastapi.testclient import TestClient

from domainweave.core.config import AppSettings, Environment, LogLevel
from domainweave.core.logging import configure_logging


@pytest.fixture(scope="session", autouse=True)
def configure_test_logging() -> None:
    """Initialise logging once for the whole test session at DEBUG level."""
    configure_logging(level="DEBUG")


@pytest.fixture()
def test_settings() -> AppSettings:
    """Return a minimal AppSettings instance configured for testing.

    Environment variables on the host machine are intentionally ignored so
    that CI and local runs produce identical behaviour.
    """
    return AppSettings(
        app_name="DomainWeave-Test",
        environment=Environment.TESTING,
        log_level=LogLevel.DEBUG,
    )


@pytest.fixture()
def test_client(test_settings: AppSettings) -> TestClient:
    """Return an httpx-backed TestClient for the FastAPI application.

    The application is created fresh from test_settings so that no host
    environment variables influence the test run.
    """
    from domainweave.main import create_app

    application = create_app(settings=test_settings)
    return TestClient(application)

