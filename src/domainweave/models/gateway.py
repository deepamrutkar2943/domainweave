"""Model Gateway — the single entry point for constructing model clients.

All graph nodes, services, and other application components that need a
language model must go through this gateway.  They must never import
provider SDKs or construct model clients directly.

Responsibilities
----------------
- Maintain a registry of approved ModelProfile objects.
- Resolve profiles by name.
- Enforce domain-level profile restrictions.
- Delegate client construction to the provider factory.
- Normalize provider errors into ModelGatewayError.
- Never log or expose API keys.
"""

from __future__ import annotations

import logging

from langchain_core.language_models.chat_models import BaseChatModel

from domainweave.core.config import AppSettings
from domainweave.core.exceptions import ModelGatewayError
from domainweave.models.providers import build_chat_model
from domainweave.models.schemas import BUILTIN_PROFILES, ModelProfile

logger = logging.getLogger("domainweave.models.gateway")


class ModelGateway:
    """Resolves model profiles and creates provider-backed chat model clients.

    Usage::

        gateway = ModelGateway(settings)
        model = gateway.get_chat_model("general_response")
        model = gateway.get_chat_model("classification", permitted_profiles=["classification"])
    """

    def __init__(
        self,
        settings: AppSettings,
        extra_profiles: list[ModelProfile] | None = None,
    ) -> None:
        """Initialise the gateway.

        Args:
            settings:       Application settings (provides provider + credentials).
            extra_profiles: Additional profiles beyond the built-ins.  Useful
                            in tests to inject fake profiles without modifying
                            BUILTIN_PROFILES.
        """
        self._settings = settings
        self._profiles: dict[str, ModelProfile] = {}

        for profile in BUILTIN_PROFILES:
            self._profiles[profile.name] = profile

        for profile in extra_profiles or []:
            self._profiles[profile.name] = profile

        logger.debug(
            "ModelGateway initialised with profiles: %s", sorted(self._profiles)
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_chat_model(
        self,
        profile_name: str,
        *,
        permitted_profiles: list[str] | None = None,
    ) -> BaseChatModel:
        """Return a ready-to-use chat model client for the named profile.

        Args:
            profile_name:       Name of the desired profile (e.g. 'classification').
            permitted_profiles: When provided, the requested profile must appear
                                in this list.  Use this to enforce domain-level
                                restrictions without passing domain config objects
                                into every caller.

        Returns:
            A :class:`BaseChatModel` configured per the profile.

        Raises:
            ModelGatewayError: If the profile is unknown, not permitted, or
                the provider client cannot be constructed.
        """
        profile = self._resolve_profile(profile_name)
        self._check_permitted(profile_name, permitted_profiles)
        api_key, base_url = self._resolve_credentials(profile)

        logger.debug(
            "Building chat model for profile '%s' (provider='%s', model='%s').",
            profile_name,
            profile.provider,
            profile.model_id,
        )

        return build_chat_model(profile, api_key=api_key, base_url=base_url)

    def list_profiles(self) -> list[str]:
        """Return the sorted list of registered profile names."""
        return sorted(self._profiles)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_profile(self, profile_name: str) -> ModelProfile:
        if profile_name not in self._profiles:
            raise ModelGatewayError(
                f"Model profile '{profile_name}' is not registered. "
                f"Available profiles: {sorted(self._profiles)}."
            )
        return self._profiles[profile_name]

    def _check_permitted(
        self, profile_name: str, permitted_profiles: list[str] | None
    ) -> None:
        if permitted_profiles is None:
            return  # no restriction applied
        if profile_name not in permitted_profiles:
            raise ModelGatewayError(
                f"Profile '{profile_name}' is not permitted in the current domain. "
                f"Permitted profiles: {permitted_profiles}."
            )

    def _resolve_credentials(self, profile: ModelProfile) -> tuple[str, str]:
        """Return (api_key, base_url) for the profile's provider from settings.

        Returns:
            A tuple of (api_key, base_url).  base_url is empty string for
            providers that use the default endpoint.

        Raises:
            ModelGatewayError: If the provider is unknown.
        """
        provider = profile.provider
        if provider == "openai":
            return self._settings.openai_api_key, ""
        if provider == "nvidia_nim":
            return self._settings.nvidia_nim_api_key, self._settings.nvidia_nim_base_url
        raise ModelGatewayError(
            f"No credential resolver for provider '{provider}'. "
            "Add a branch in ModelGateway._resolve_credentials()."
        )
