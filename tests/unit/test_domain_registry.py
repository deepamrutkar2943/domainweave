"""Unit tests for the Domain Registry."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from configs.domains.schemas import DomainConfig

from domainweave.core.exceptions import ConfigurationError, DomainNotFoundError
from domainweave.domains.registry import DomainRegistry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def write_domain_yaml(tmp_path: Path, filename: str, content: str) -> Path:
    """Write a YAML file to tmp_path and return its path."""
    path = tmp_path / filename
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


VALID_YAML = """\
    domain_id: test_domain
    version: "1.0"
    display_name: "Test Domain"
    description: "Used in unit tests."
    permitted_model_profiles:
      - classification
      - general_response
    enabled_capabilities: []
    knowledge_collections: []
    policies:
      max_tool_calls_per_run: 3
      require_citations: false
      allow_multi_step: false
"""


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


class TestDomainConfig:
    def test_valid_config_parses(self) -> None:
        cfg = DomainConfig(
            domain_id="hr_support",
            version="1.0",
            display_name="HR Support",
        )
        assert cfg.domain_id == "hr_support"
        assert cfg.permitted_model_profiles == []

    def test_domain_id_must_be_lowercase(self) -> None:
        with pytest.raises((ValueError, TypeError), match="lower-case"):
            DomainConfig(domain_id="HR_Support", version="1.0", display_name="x")

    def test_domain_id_must_not_be_empty(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            DomainConfig(domain_id="", version="1.0", display_name="x")

    def test_domain_id_must_not_contain_spaces(self) -> None:
        with pytest.raises((ValueError, TypeError), match="spaces"):
            DomainConfig(domain_id="my domain", version="1.0", display_name="x")

    def test_frozen_model(self) -> None:
        cfg = DomainConfig(domain_id="general", version="1.0", display_name="General")
        with pytest.raises((ValueError, TypeError)):
            cfg.domain_id = "other"  # type: ignore[misc]

    def test_policies_have_defaults(self) -> None:
        cfg = DomainConfig(domain_id="general", version="1.0", display_name="General")
        assert cfg.policies.max_tool_calls_per_run == 5
        assert cfg.policies.require_citations is False

    def test_blank_profile_name_rejected(self) -> None:
        with pytest.raises((ValueError, TypeError), match="blank"):
            DomainConfig(
                domain_id="general",
                version="1.0",
                display_name="General",
                permitted_model_profiles=["classification", ""],
            )


# ---------------------------------------------------------------------------
# Registry loading tests
# ---------------------------------------------------------------------------


class TestDomainRegistryLoading:
    def test_load_valid_file(self, tmp_path: Path) -> None:
        write_domain_yaml(tmp_path, "test_domain.yaml", VALID_YAML)
        registry = DomainRegistry(tmp_path)
        registry.load()
        assert "test_domain" in registry.list_domains()

    def test_get_domain_returns_config(self, tmp_path: Path) -> None:
        write_domain_yaml(tmp_path, "test_domain.yaml", VALID_YAML)
        registry = DomainRegistry(tmp_path)
        registry.load()
        domain = registry.get_domain("test_domain")
        assert isinstance(domain, DomainConfig)
        assert domain.display_name == "Test Domain"

    def test_load_empty_directory_does_not_raise(self, tmp_path: Path) -> None:
        registry = DomainRegistry(tmp_path)
        registry.load()  # warns but does not raise
        assert registry.list_domains() == []

    def test_load_multiple_domains(self, tmp_path: Path) -> None:
        write_domain_yaml(tmp_path, "test_domain.yaml", VALID_YAML)
        write_domain_yaml(
            tmp_path,
            "another.yaml",
            """\
            domain_id: another
            version: "1.0"
            display_name: "Another"
            """,
        )
        registry = DomainRegistry(tmp_path)
        registry.load()
        assert sorted(registry.list_domains()) == ["another", "test_domain"]

    def test_missing_directory_raises_config_error(self, tmp_path: Path) -> None:
        registry = DomainRegistry(tmp_path / "nonexistent")
        with pytest.raises(ConfigurationError, match="not found"):
            registry.load()

    def test_duplicate_domain_id_raises_config_error(self, tmp_path: Path) -> None:
        write_domain_yaml(tmp_path, "test_domain.yaml", VALID_YAML)
        write_domain_yaml(tmp_path, "test_domain_copy.yaml", VALID_YAML)
        registry = DomainRegistry(tmp_path)
        with pytest.raises(ConfigurationError, match="Duplicate"):
            registry.load()

    def test_invalid_yaml_raises_config_error(self, tmp_path: Path) -> None:
        (tmp_path / "bad.yaml").write_text(":\ninvalid: [yaml", encoding="utf-8")
        registry = DomainRegistry(tmp_path)
        with pytest.raises(ConfigurationError, match="YAML parse error"):
            registry.load()

    def test_invalid_schema_raises_config_error(self, tmp_path: Path) -> None:
        write_domain_yaml(
            tmp_path,
            "bad_schema.yaml",
            """\
            domain_id: "Bad Schema"
            version: "1.0"
            display_name: "bad"
            """,
        )
        registry = DomainRegistry(tmp_path)
        with pytest.raises(ConfigurationError, match="Validation failed"):
            registry.load()

    def test_non_dict_yaml_raises_config_error(self, tmp_path: Path) -> None:
        (tmp_path / "list.yaml").write_text("- item1\n- item2\n", encoding="utf-8")
        registry = DomainRegistry(tmp_path)
        with pytest.raises(ConfigurationError, match="mapping"):
            registry.load()

    def test_get_before_load_raises_config_error(self, tmp_path: Path) -> None:
        registry = DomainRegistry(tmp_path)
        with pytest.raises(ConfigurationError, match="load\\(\\)"):
            registry.get_domain("general")

    def test_get_unknown_domain_raises_not_found(self, tmp_path: Path) -> None:
        write_domain_yaml(tmp_path, "test_domain.yaml", VALID_YAML)
        registry = DomainRegistry(tmp_path)
        registry.load()
        with pytest.raises(DomainNotFoundError) as exc_info:
            registry.get_domain("nonexistent")
        assert exc_info.value.domain_id == "nonexistent"

    def test_is_loaded_flag(self, tmp_path: Path) -> None:
        registry = DomainRegistry(tmp_path)
        assert registry.is_loaded is False
        registry.load()
        assert registry.is_loaded is True
