"""Unit tests for Model Gateway, profiles, and provider factory.

All tests use fake/mock models — no real API keys or network calls.
"""

from __future__ import annotations

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from pytest_mock import MockerFixture

from domainweave.core.config import AppSettings, Environment
from domainweave.core.exceptions import ModelGatewayError
from domainweave.models.gateway import ModelGateway
from domainweave.models.providers import SUPPORTED_PROVIDERS, build_chat_model
from domainweave.models.schemas import BUILTIN_PROFILES, ModelProfile

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def fake_settings(**overrides: object) -> AppSettings:
    """Return test AppSettings with a dummy API key so validation passes."""
    defaults = {
        "environment": Environment.TESTING,
        "openai_api_key": "sk-test-fake-key",
        "nvidia_nim_api_key": "",
    }
    defaults.update(overrides)
    return AppSettings(**defaults)  # type: ignore[arg-type]


def fake_profile(**overrides: object) -> ModelProfile:
    """Return a ModelProfile suitable for tests."""
    defaults = {
        "name": "test_profile",
        "provider": "openai",
        "model_id": "gpt-4o-mini",
        "temperature": 0.0,
        "max_tokens": 256,
        "timeout": 10.0,
        "max_retries": 0,
    }
    defaults.update(overrides)
    return ModelProfile(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# ModelProfile schema tests
# ---------------------------------------------------------------------------


class TestModelProfileSchema:
    def test_builtin_profiles_are_valid(self) -> None:
        """All built-in profiles must parse without error."""
        assert len(BUILTIN_PROFILES) >= 2
        names = {p.name for p in BUILTIN_PROFILES}
        assert "classification" in names
        assert "general_response" in names

    def test_temperature_bounds(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            fake_profile(temperature=3.0)

    def test_max_retries_bounds(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            fake_profile(max_retries=10)

    def test_frozen_profile(self) -> None:
        profile = fake_profile()
        with pytest.raises((ValueError, TypeError)):
            profile.temperature = 1.0  # type: ignore[misc]

    def test_timeout_must_be_positive(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            fake_profile(timeout=0.0)


# ---------------------------------------------------------------------------
# Provider factory tests (mocked — no real network)
# ---------------------------------------------------------------------------


class TestProviderFactory:
    def test_unsupported_provider_raises(self) -> None:
        profile = fake_profile(provider="unknown_provider")
        with pytest.raises(ModelGatewayError, match="not supported"):
            build_chat_model(profile, api_key="key")

    def test_missing_api_key_raises(self) -> None:
        profile = fake_profile(provider="openai")
        with pytest.raises(ModelGatewayError, match="API key"):
            build_chat_model(profile, api_key="")

    def test_supported_providers_set(self) -> None:
        assert "openai" in SUPPORTED_PROVIDERS
        assert "nvidia_nim" in SUPPORTED_PROVIDERS

    def test_openai_client_constructed(self, mocker: MockerFixture) -> None:
        """Verify ChatOpenAI is constructed with correct kwargs."""
        mock_cls = mocker.patch("langchain_openai.ChatOpenAI")
        mock_cls.return_value = mocker.MagicMock(spec=BaseChatModel)

        profile = fake_profile(provider="openai", model_id="gpt-4o-mini")
        build_chat_model(profile, api_key="sk-fake")

        mock_cls.assert_called_once()
        call_kwargs = mock_cls.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert call_kwargs["api_key"] == "sk-fake"
        assert "base_url" not in call_kwargs  # no override for vanilla OpenAI

    def test_nvidia_nim_passes_base_url(self, mocker: MockerFixture) -> None:
        """Verify base_url is forwarded for NVIDIA NIM."""
        mock_cls = mocker.patch("langchain_openai.ChatOpenAI")
        mock_cls.return_value = mocker.MagicMock(spec=BaseChatModel)

        profile = fake_profile(provider="nvidia_nim", model_id="meta/llama-3.1-8b-instruct")
        build_chat_model(
            profile,
            api_key="nvapi-fake",
            base_url="https://integrate.api.nvidia.com/v1",
        )

        call_kwargs = mock_cls.call_args.kwargs
        assert call_kwargs["base_url"] == "https://integrate.api.nvidia.com/v1"


# ---------------------------------------------------------------------------
# ModelGateway tests
# ---------------------------------------------------------------------------


class TestModelGateway:
    def test_list_profiles_includes_builtins(self) -> None:
        gateway = ModelGateway(fake_settings())
        profiles = gateway.list_profiles()
        assert "classification" in profiles
        assert "general_response" in profiles

    def test_unknown_profile_raises(self) -> None:
        gateway = ModelGateway(fake_settings())
        with pytest.raises(ModelGatewayError, match="not registered"):
            gateway.get_chat_model("nonexistent_profile")

    def test_profile_not_in_permitted_raises(self) -> None:
        gateway = ModelGateway(fake_settings())
        with pytest.raises(ModelGatewayError, match="not permitted"):
            gateway.get_chat_model(
                "general_response",
                permitted_profiles=["classification"],
            )

    def test_permitted_profiles_none_allows_all(self, mocker: MockerFixture) -> None:
        mocker.patch("langchain_openai.ChatOpenAI")
        gateway = ModelGateway(fake_settings())
        # Should not raise — no domain restriction applied
        gateway.get_chat_model("classification", permitted_profiles=None)

    def test_get_model_with_valid_profile(self, mocker: MockerFixture) -> None:
        mock_cls = mocker.patch("langchain_openai.ChatOpenAI")
        mock_cls.return_value = mocker.MagicMock(spec=BaseChatModel)

        gateway = ModelGateway(fake_settings(openai_api_key="sk-fake"))
        model = gateway.get_chat_model("classification")
        assert model is mock_cls.return_value

    def test_missing_api_key_for_openai_raises(self) -> None:
        gateway = ModelGateway(fake_settings(openai_api_key=""))
        with pytest.raises(ModelGatewayError, match="API key"):
            gateway.get_chat_model("classification")

    def test_nvidia_nim_credentials_forwarded(self, mocker: MockerFixture) -> None:
        mock_cls = mocker.patch("langchain_openai.ChatOpenAI")
        mock_cls.return_value = mocker.MagicMock(spec=BaseChatModel)

        nim_profile = ModelProfile(
            name="nim_test",
            provider="nvidia_nim",
            model_id="meta/llama-3.1-8b-instruct",
        )
        gateway = ModelGateway(
            fake_settings(nvidia_nim_api_key="nvapi-fake"),
            extra_profiles=[nim_profile],
        )
        gateway.get_chat_model("nim_test")

        call_kwargs = mock_cls.call_args.kwargs
        assert call_kwargs["api_key"] == "nvapi-fake"
        assert "integrate.api.nvidia.com" in call_kwargs["base_url"]

    def test_extra_profiles_registered(self) -> None:
        custom = fake_profile(name="custom_profile")
        gateway = ModelGateway(fake_settings(), extra_profiles=[custom])
        assert "custom_profile" in gateway.list_profiles()

    def test_extra_profile_overrides_builtin(self, mocker: MockerFixture) -> None:
        """An extra profile with the same name as a builtin replaces it."""
        mocker.patch("langchain_openai.ChatOpenAI")
        custom = fake_profile(name="classification", model_id="gpt-3.5-turbo")
        gateway = ModelGateway(fake_settings(), extra_profiles=[custom])
        # Should not raise; the custom profile is used
        gateway.get_chat_model("classification")
