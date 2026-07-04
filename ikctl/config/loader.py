"""Loads ~/.ikctl/config and returns a typed IkctlConfig."""
from __future__ import annotations

import logging
import pathlib

from envyaml import EnvYAML

from ikctl.exceptions import ConfigError
from ikctl.config.models import Context, IkctlConfig

_logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_PATH = pathlib.Path.home() / ".ikctl" / "config"


class ConfigLoader:
    """Reads and parses the ikctl configuration file."""

    def __init__(self, config_path: pathlib.Path | None = None) -> None:
        self._config_path = config_path or _DEFAULT_CONFIG_PATH

    def load(self) -> IkctlConfig:
        """Loads ~/.ikctl/config and returns a validated IkctlConfig.

        Raises ConfigError if the file does not exist or is malformed.
        """
        if not self._config_path.exists():
            raise ConfigError(f"Config file not found: {self._config_path}")

        try:
            raw = EnvYAML(str(self._config_path), strict=False)
        except Exception as exc:
            raise ConfigError(f"Failed to parse config file: {self._config_path}: {exc}") from exc

        try:
            current_context = raw["context"]
            raw_contexts: dict = raw["contexts"]
        except (KeyError, TypeError) as exc:
            raise ConfigError(f"Malformed config file — missing key: {exc}") from exc

        contexts: dict[str, Context] = {}
        for ctx_name, ctx_data in raw_contexts.items():
            try:
                raw_exclude = ctx_data.get("exclude", [])
                contexts[ctx_name] = Context(
                    name=ctx_name,
                    path_kits=ctx_data.get("path_kits", ""),
                    path_servers=ctx_data.get("path_servers", ""),
                    path_secrets=ctx_data.get("path_secrets", ""),
                    mode=ctx_data.get("mode", "remote"),
                    timeout_connect=float(ctx_data.get("timeout_connect", 30.0)),
                    timeout_exec=float(ctx_data.get("timeout_exec", 120.0)),
                    exclude=list(raw_exclude) if raw_exclude else [],
                    kits_repo=ctx_data.get("kits_repo") or None,
                    kits_ref=str(ctx_data.get("kits_ref", "main")),
                    kits_token=ctx_data.get("kits_token") or None,
                    path_pipelines=ctx_data.get("path_pipelines") or None,
                )
            except Exception as exc:
                raise ConfigError(
                    f"Malformed context '{ctx_name}' in config: {exc}"
                ) from exc

        _logger.debug("Config loaded: context=%s, contexts=%s", current_context, list(contexts))
        return IkctlConfig(context=current_context, contexts=contexts)
