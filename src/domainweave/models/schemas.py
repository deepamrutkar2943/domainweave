"""Pydantic schemas for Model Gateway profiles.

A ModelProfile is a named, validated configuration bundle that describes
how to construct a model client for a specific logical role.  Business
logic references profiles by name (e.g. 'classification') and never
constructs model clients directly.

Profiles are defined in code (not in YAML) because they are platform-level
concerns, not domain-level concerns.  A domain can restrict which profiles
it is allowed to use, but it cannot define new ones.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ModelProfile(BaseModel):
    """Describes one logical model role and its construction parameters.

    Instances are immutable after creation.  The Model Gateway holds a
    registry of these and resolves them by name.
    """

    model_config = {"frozen": True}

    name: str = Field(
        description="Stable profile name used by all callers (e.g. 'classification')."
    )
    provider: str = Field(
        description="Provider identifier. Supported: 'openai', 'nvidia_nim'."
    )
    model_id: str = Field(
        description="Provider-specific model identifier (e.g. 'gpt-4o-mini')."
    )
    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Sampling temperature. 0.0 = deterministic.",
    )
    max_tokens: int = Field(
        default=1024,
        ge=1,
        le=32768,
        description="Maximum tokens in the model response.",
    )
    timeout: float = Field(
        default=30.0,
        gt=0,
        description="Request timeout in seconds.",
    )
    max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Number of transient-error retries before raising.",
    )


# ---------------------------------------------------------------------------
# Built-in profile definitions
#
# These are the platform-level profiles available to all domains that permit
# them.  Add new profiles here when a new logical role is required.
# Keep secrets OUT of these objects — credentials come from AppSettings.
# ---------------------------------------------------------------------------

BUILTIN_PROFILES: list[ModelProfile] = [
    ModelProfile(
        name="classification",
        provider="openai",
        model_id="gpt-4o-mini",
        temperature=0.0,
        max_tokens=256,
        timeout=15.0,
        max_retries=2,
    ),
    ModelProfile(
        name="general_response",
        provider="openai",
        model_id="gpt-4o-mini",
        temperature=0.7,
        max_tokens=1024,
        timeout=30.0,
        max_retries=2,
    ),
]
