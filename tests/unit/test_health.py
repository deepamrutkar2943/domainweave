"""Unit tests for the GET /health endpoint and application factory."""

from fastapi.testclient import TestClient

from domainweave.core.config import AppSettings, Environment


class TestHealthEndpoint:
    """Verify /health returns correct status and metadata."""

    def test_health_returns_200(self, test_client: TestClient) -> None:
        response = test_client.get("/health")
        assert response.status_code == 200

    def test_health_body_status_ok(self, test_client: TestClient) -> None:
        response = test_client.get("/health")
        body = response.json()
        assert body["status"] == "ok"

    def test_health_body_contains_app_name(self, test_client: TestClient) -> None:
        response = test_client.get("/health")
        body = response.json()
        assert body["app_name"] == "DomainWeave-Test"

    def test_health_body_contains_version(self, test_client: TestClient) -> None:
        response = test_client.get("/health")
        body = response.json()
        assert "version" in body
        assert isinstance(body["version"], str)

    def test_health_body_contains_environment(self, test_client: TestClient) -> None:
        response = test_client.get("/health")
        body = response.json()
        assert body["environment"] == Environment.TESTING.value

    def test_health_content_type_is_json(self, test_client: TestClient) -> None:
        response = test_client.get("/health")
        assert "application/json" in response.headers["content-type"]


class TestCreateApp:
    """Verify the application factory behaves correctly with injected settings."""

    def test_docs_available_in_non_production(self) -> None:
        from domainweave.main import create_app

        app = create_app(settings=AppSettings(environment=Environment.DEVELOPMENT))
        client = TestClient(app)
        response = client.get("/docs")
        assert response.status_code == 200

    def test_docs_disabled_in_production(self) -> None:
        from domainweave.main import create_app

        app = create_app(settings=AppSettings(environment=Environment.PRODUCTION))
        client = TestClient(app)
        response = client.get("/docs")
        assert response.status_code == 404

    def test_settings_attached_to_app_state(self) -> None:
        from domainweave.main import create_app

        settings = AppSettings(app_name="StateTest")
        app = create_app(settings=settings)
        assert app.state.settings.app_name == "StateTest"

