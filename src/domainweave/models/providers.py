"""Provider factory for the Model Gateway.

This module is the ONLY place in the codebase that imports provider-specific
LangChain packages.  All other modules interact with the abstract
BaseChatModel interface from langchain-core.

Supported providers
-------------------
- openai      : OpenAI API (requires OPENAI_API_KEY)
- nvidia_nim  : NVIDIA NIM OpenAI-compatible endpoint (requires
                NVIDIA_NIM_API_KEY and optionally NVIDIA_NIM_BASE_URL)

Adding a new provider
---------------------
1. Add its LangChain integration package to pyproject.toml.
2. Add a branch in _build_openai_compatible() or a new private builder.
3. Update the SUPPORTED_PROVIDERS set.
4. Document the required environment variables in .env.example.
"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from domainweave.core.exceptions import ModelGatewayError
from domainweave.models.schemas import ModelProfile

SUPPORTED_PROVIDERS: frozenset[str] = frozenset({"openai", "nvidia_nim"})


def build_chat_model(profile: ModelProfile, *, api_key: str, base_url: str = "") -> BaseChatModel:
    """Construct a LangChain chat model client for the given profile.

    Args:
        profile:  The validated ModelProfile describing model settings.
        api_key:  The provider API key resolved from AppSettings (never
                  hardcoded here).
        base_url: Optional base URL override (used for NVIDIA NIM).

    Returns:
        A :class:`BaseChatModel` instance ready for invocation.

    Raises:
        ModelGatewayError: If the provider is unsupported, the API key is
            missing, or the client cannot be constructed.
    """
    if profile.provider not in SUPPORTED_PROVIDERS:
        raise ModelGatewayError(
            f"Provider '{profile.provider}' is not supported. "
            f"Supported providers: {sorted(SUPPORTED_PROVIDERS)}."
        )

    if not api_key:
        raise ModelGatewayError(
            f"No API key configured for provider '{profile.provider}'. "
            "Set the corresponding environment variable."
        )

    try:
        return _build_openai_compatible(profile, api_key=api_key, base_url=base_url)
    except Exception as exc:
        # Wrap provider-specific errors so callers never depend on SDK details.
        raise ModelGatewayError(
            f"Failed to initialise model client for profile '{profile.name}' "
            f"(provider='{profile.provider}'): {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Private builders — one per provider family
# ---------------------------------------------------------------------------


def _build_openai_compatible(
    profile: ModelProfile, *, api_key: str, base_url: str
) -> BaseChatModel:
    """Build a ChatOpenAI client for OpenAI or any OpenAI-compatible endpoint."""
    # Import here so that the package is only required when actually used.
    from langchain_openai import ChatOpenAI  # noqa: PLC0415

    kwargs: dict[str, object] = {
        "model": profile.model_id,
        "temperature": profile.temperature,
        "max_tokens": profile.max_tokens,
        "timeout": profile.timeout,
        "max_retries": profile.max_retries,
        "api_key": api_key,
    }
    if base_url:
        kwargs["base_url"] = base_url

    return ChatOpenAI(**kwargs)  # type: ignore[arg-type]
