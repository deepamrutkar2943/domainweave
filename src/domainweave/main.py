"""DomainWeave application entry point.

This module:
- Initializes logging exactly once, before any other module uses a logger.
- Loads and validates application settings.
- Creates the FastAPI application instance.
- Registers API routes.
- Exposes a `main()` function for the console-script entry point.

FastAPI is responsible for HTTP concerns only.  Agent orchestration is
intentionally absent from this module; it belongs in the runtime layer.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from domainweave.core.config import AppSettings, get_settings
from domainweave.core.logging import configure_logging, get_logger

# ---------------------------------------------------------------------------
# Bootstrap: logging must be configured before any module-level logger usage.
# ---------------------------------------------------------------------------
_bootstrap_settings = get_settings()
configure_logging(level=_bootstrap_settings.log_level.value)

logger = get_logger("main")

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app(settings: AppSettings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Optional settings override, useful in tests.  When None,
                  settings are loaded from the environment.

    Returns:
        A configured :class:`fastapi.FastAPI` instance.
    """
    cfg = settings or get_settings()

    app = FastAPI(
        title=cfg.app_name,
        version=cfg.app_version,
        description="Domain-agnostic, modular Agentic AI Platform",
        docs_url="/docs" if not cfg.is_production else None,
        redoc_url="/redoc" if not cfg.is_production else None,
    )

    # Attach settings to app state so route handlers can access them without
    # importing get_settings() directly.
    app.state.settings = cfg

    _register_routes(app)

    logger.info(
        "Application created",
        extra={
            "app_name": cfg.app_name,
            "version": cfg.app_version,
            "environment": cfg.environment.value,
        },
    )
    return app


def _register_routes(app: FastAPI) -> None:
    """Attach all route handlers to the application."""

    @app.get(
        "/health",
        summary="Health check",
        response_description="Returns service liveness and basic metadata.",
        tags=["Operations"],
    )
    async def health() -> JSONResponse:
        """Liveness probe endpoint.

        Returns HTTP 200 with a JSON body when the application process is
        running and its configuration loaded successfully.  This endpoint
        does **not** check downstream dependencies (database, model
        providers); those belong in a separate readiness probe added in a
        later milestone.
        """
        cfg: AppSettings = app.state.settings
        return JSONResponse(
            content={
                "status": "ok",
                "app_name": cfg.app_name,
                "version": cfg.app_version,
                "environment": cfg.environment.value,
            }
        )


# ---------------------------------------------------------------------------
# Module-level app instance (used by uvicorn and the console-script entry point)
# ---------------------------------------------------------------------------
app = create_app()


def main() -> None:
    """Console-script entry point registered in pyproject.toml."""
    cfg = app.state.settings
    uvicorn.run(
        "domainweave.main:app",
        host=cfg.api_host,
        port=cfg.api_port,
        reload=cfg.is_development,
        log_level=cfg.log_level.value.lower(),
    )


if __name__ == "__main__":
    main()
