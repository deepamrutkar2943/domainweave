"""Pydantic schemas for domain configuration.

A domain configuration file (YAML) is the primary way to onboard a new
business domain without modifying shared platform code.  Every field is
validated on load so configuration errors surface immediately at startup,
not during a live request.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class DomainPolicies(BaseModel):
    """Domain-level policy overrides.

    All fields have platform-wide defaults.  A domain YAML only needs to
    specify values that differ from those defaults.
    """

    max_tool_calls_per_run: int = Field(
        default=5,
        ge=0,
        le=50,
        description="Maximum number of tool calls allowed within a single run.",
    )
    require_citations: bool = Field(
        default=False,
        description="When True, the Response Synthesizer must include source citations.",
    )
    allow_multi_step: bool = Field(
        default=False,
        description="When True, the Planner may generate multi-step execution plans.",
    )


class DomainConfig(BaseModel):
    """Validated representation of one domain's YAML configuration file.

    Instances are created by the Domain Registry after loading and parsing
    a YAML file.  They are immutable after construction.
    """

    model_config = {"frozen": True}

    domain_id: str = Field(
        description="Stable, lower-snake-case identifier for the domain (e.g. 'hr_support')."
    )
    version: str = Field(description="Configuration schema version string (e.g. '1.0').")
    display_name: str = Field(description="Human-readable domain name shown in UIs and logs.")
    description: str = Field(default="", description="Short description of the domain's purpose.")

    permitted_model_profiles: list[str] = Field(
        default_factory=list,
        description="Model profile names this domain may use. Must match registered profiles.",
    )
    enabled_capabilities: list[str] = Field(
        default_factory=list,
        description="Capability identifiers available to this domain.",
    )
    knowledge_collections: list[str] = Field(
        default_factory=list,
        description="Knowledge collection identifiers accessible to this domain.",
    )
    policies: DomainPolicies = Field(
        default_factory=DomainPolicies,
        description="Domain-level policy overrides.",
    )

    @field_validator("domain_id")
    @classmethod
    def validate_domain_id(cls, value: str) -> str:
        """Enforce lower-snake-case domain identifiers."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("domain_id must not be empty.")
        if stripped != stripped.lower():
            raise ValueError(
                f"domain_id must be lower-case. Got: '{stripped}'. "
                f"Use '{stripped.lower()}' instead."
            )
        if " " in stripped:
            raise ValueError(
                f"domain_id must not contain spaces. Got: '{stripped}'. "
                "Use underscores instead."
            )
        return stripped

    @field_validator("permitted_model_profiles")
    @classmethod
    def validate_profiles_not_empty_strings(cls, values: list[str]) -> list[str]:
        """Reject lists that contain blank profile name entries."""
        for v in values:
            if not v.strip():
                raise ValueError("permitted_model_profiles must not contain blank entries.")
        return values