"""Domain Registry — loads and validates domain configurations from YAML files.

The registry is the single source of truth for which domains are available
and what each domain is permitted to do.  It is intentionally stateless
after initialisation: load once, read many times.

Loading rules:
- Every .yaml / .yml file in the configured directory is treated as one domain.
- The domain_id inside the file must match the filename stem.
- Duplicate domain IDs across files are a fatal configuration error.
- Unknown or missing directories raise ConfigurationError at startup.
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml
from configs.domains.schemas import DomainConfig
from pydantic import ValidationError

from domainweave.core.exceptions import ConfigurationError, DomainNotFoundError

logger = logging.getLogger("domainweave.domains.registry")


class DomainRegistry:
    """Loads, validates, and provides access to domain configurations.

    Usage::

        registry = DomainRegistry(config_dir="configs/domains")
        registry.load()                          # call once at startup
        domain = registry.get_domain("general")  # fast dict lookup
    """

    def __init__(self, config_dir: str | Path) -> None:
        self._config_dir = Path(config_dir)
        self._domains: dict[str, DomainConfig] = {}
        self._loaded = False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Discover and validate all domain YAML files in the config directory.

        Raises:
            ConfigurationError: If the directory does not exist, a file
                cannot be parsed, validation fails, or duplicate domain IDs
                are found.
        """
        if not self._config_dir.exists():
            raise ConfigurationError(
                f"Domain config directory not found: '{self._config_dir}'. "
                "Set DOMAINS_CONFIG_DIR to a valid path."
            )
        if not self._config_dir.is_dir():
            raise ConfigurationError(
                f"Domain config path is not a directory: '{self._config_dir}'."
            )

        yaml_files = sorted(
            [p for p in self._config_dir.iterdir() if p.suffix in {".yaml", ".yml"}]
        )

        if not yaml_files:
            logger.warning("No domain YAML files found in '%s'.", self._config_dir)

        loaded: dict[str, DomainConfig] = {}
        for path in yaml_files:
            domain = self._load_file(path)
            if domain.domain_id in loaded:
                raise ConfigurationError(
                    f"Duplicate domain_id '{domain.domain_id}' found in '{path}'. "
                    f"Already registered from another file."
                )
            self._validate_filename_matches_id(path, domain.domain_id)
            loaded[domain.domain_id] = domain
            logger.debug("Loaded domain '%s' from '%s'.", domain.domain_id, path.name)

        self._domains = loaded
        self._loaded = True
        logger.info("Domain Registry loaded %d domain(s).", len(self._domains))

    def get_domain(self, domain_id: str) -> DomainConfig:
        """Return the validated config for a registered domain.

        Args:
            domain_id: The stable domain identifier (e.g. 'general').

        Returns:
            The frozen :class:`DomainConfig` for that domain.

        Raises:
            DomainNotFoundError: If the domain_id is not registered.
            ConfigurationError: If :meth:`load` has not been called yet.
        """
        self._ensure_loaded()
        if domain_id not in self._domains:
            raise DomainNotFoundError(domain_id)
        return self._domains[domain_id]

    def list_domains(self) -> list[str]:
        """Return the sorted list of registered domain IDs."""
        self._ensure_loaded()
        return sorted(self._domains)

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_file(self, path: Path) -> DomainConfig:
        """Parse one YAML file and return a validated DomainConfig."""
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ConfigurationError(
                f"Cannot read domain config file '{path}': {exc}"
            ) from exc

        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            raise ConfigurationError(
                f"YAML parse error in '{path}': {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise ConfigurationError(
                f"Domain config file '{path}' must contain a YAML mapping, got {type(data).__name__}."
            )

        try:
            return DomainConfig(**data)
        except ValidationError as exc:
            # Surface only field-level messages; no internal stack detail.
            errors = "; ".join(
                f"{'.'.join(str(part) for part in e['loc'])}: {e['msg']}"
                for e in exc.errors()
            )
            raise ConfigurationError(
                f"Validation failed for domain config '{path}': {errors}"
            ) from exc

    def _validate_filename_matches_id(self, path: Path, domain_id: str) -> None:
        """Warn (not error) when the filename stem doesn't match domain_id.

        We warn rather than raise so that accidental renames don't crash
        production but are still surfaced in logs.
        """
        stem = path.stem
        if stem != domain_id:
            logger.warning(
                "Domain config filename '%s' does not match domain_id '%s'. "
                "Rename the file to '%s.yaml' to avoid confusion.",
                path.name,
                domain_id,
                domain_id,
            )

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            raise ConfigurationError(
                "DomainRegistry.load() has not been called. "
                "Call load() before accessing domain configurations."
            )
