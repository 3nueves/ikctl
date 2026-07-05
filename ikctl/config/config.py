"""Backward-compatible Config facade delegating to the new SOLID classes."""
from __future__ import annotations

import logging
import pathlib
import sys

from envyaml import EnvYAML

from ikctl.config.bootstrap import ConfigBootstrap
from ikctl.exceptions import ConfigError, KitNotFoundError, ServerNotFoundError
from ikctl.config.kit_repo import KitRepository
from ikctl.config.loader import ConfigLoader
from ikctl.config.models import KitPipeline

__version__ = "1.9.0"

_logger = logging.getLogger(__name__)


class Config:
    """Backward-compatible configuration facade.

    Delegates to ConfigLoader, ConfigBootstrap, KitRepository and ServerRepository.
    Raises domain exceptions (ServerNotFoundError, KitNotFoundError, ConfigError) on error.
    """

    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)
        self.version = __version__
        self.home = pathlib.Path.home()
        self.path_config_file = self.home / ".ikctl" / "config"

        bootstrap = ConfigBootstrap(interactive=True)
        bootstrap.setup()

        try:
            loader = ConfigLoader(config_path=self.path_config_file)
            self._ikctl_config = loader.load()
        except ConfigError as exc:
            print(f"\n{exc}\n", file=sys.stderr)
            sys.exit(1)

        self.context = self._ikctl_config.context

    def load_config_file_mode(self) -> str:
        """Returns the mode ('local' or 'remote') for the active context."""
        try:
            return self._ikctl_config.contexts[self.context].mode
        except KeyError as exc:
            print(f"\n keyError: {exc} has a mistake\n", file=sys.stderr)
            sys.exit(1)

    def load_timeout_connect(self) -> float:
        """Returns timeout_connect for the active context (default 30.0)."""
        try:
            return self._ikctl_config.contexts[self.context].timeout_connect
        except KeyError:
            return 30.0

    def load_timeout_exec(self) -> float:
        """Returns timeout_exec for the active context (default 120.0)."""
        try:
            return self._ikctl_config.contexts[self.context].timeout_exec
        except KeyError:
            return 120.0

    def load_config_file_kits(self) -> tuple:
        """Returns (kits_dict, path_kits) for the active context using auto-discovery."""
        try:
            path_kits = self._ikctl_config.contexts[self.context].path_kits
        except KeyError as exc:
            print(f"\n keyError: {exc} has a mistake\n", file=sys.stderr)
            sys.exit(1)

        repo = KitRepository(self._ikctl_config)
        discovered = repo.list_kits()
        kits_dict = {"kits": [f"{name}/ikctl.yaml" for name in discovered]}
        return kits_dict, path_kits

    def load_config_file_servers(self) -> tuple:
        """Returns (servers_envyaml, path_servers) for the active context."""
        try:
            path_servers = self._ikctl_config.contexts[self.context].path_servers
        except KeyError as exc:
            print(f"\n keyError: {exc} has a mistake\n", file=sys.stderr)
            sys.exit(1)

        try:
            return EnvYAML(path_servers + "/config.yaml", strict=False), path_servers
        except Exception as exc:
            raise ConfigError(f"[ikctl - servers config] {exc}") from exc

    def extract_config_servers(self, config: object, group: str | None = None) -> dict:
        """Extracts a ServerGroup dict from the raw servers config.

        When group is None returns the FIRST group, not the last (bug fix).
        """
        hosts: list[str] = []
        user = "root"
        port = 22
        password: str | None = None
        pkey = None

        for entry in config["servers"]:
            if group == entry["name"] or group is None:
                user = entry.get("user", "root")
                port = entry.get("port", 22)
                password = entry.get("password") or None
                pkey = entry.get("pkey", None)
                if entry.get("hosts"):
                    hosts = list(entry["hosts"])
                if group is None:
                    break

        if not hosts:
            raise ServerNotFoundError("Host not found")

        return {
            "user": user,
            "port": port,
            "pkey": pkey,
            "hosts": hosts,
            "password": password,
        }

    def extract_config_kits(self, config: object, name_kit: str) -> tuple:
        """Extracts (uploads, pipeline) lists for the named kit using auto-discovery."""
        repo = KitRepository(self._ikctl_config)
        try:
            kit_pipeline = repo.resolve(name_kit)
        except KitNotFoundError:
            raise
        return kit_pipeline.uploads, kit_pipeline.pipeline

    def load_path_pipelines(self) -> str | None:
        """Returns path_pipelines for the active context, or None if not set."""
        try:
            return self._ikctl_config.contexts[self.context].path_pipelines
        except KeyError:
            return None

    def load_kit_pipelines(self) -> dict:
        """Returns a dict mapping kit name to KitPipeline for the active context."""
        repo = KitRepository(self._ikctl_config)
        kit_names = repo.list_kits()
        result: dict[str, KitPipeline] = {}
        for name in kit_names:
            try:
                result[name] = repo.resolve(name)
            except Exception:
                pass
        return result

    def extract_secrets(self) -> tuple[str, str]:
        """Returns (secrets_content, path_secrets) for the active context."""
        path_secrets = self._ikctl_config.contexts[self.context].path_secrets
        if not path_secrets:
            return "", ""
        try:
            with open(path_secrets, "a+", encoding="utf-8") as f:
                f.seek(0)
                secrets = f.readlines()
        except FileNotFoundError as exc:
            self._logger.error("Secrets file not found: %s", exc)
            return "", path_secrets
        secrets_str = "".join(secrets).strip()
        return secrets_str, path_secrets

    # Keep old typo names as aliases so any existing callers still work.
    def extrac_config_kits(self, config: object, name_kit: str) -> tuple:
        """Alias for extract_config_kits (typo preserved for backward compatibility)."""
        return self.extract_config_kits(config, name_kit)

    def extrac_secrets(self) -> tuple[str, str]:
        """Alias for extract_secrets (typo preserved for backward compatibility)."""
        return self.extract_secrets()
