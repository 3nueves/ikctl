"""Creates the initial ~/.ikctl/ folder structure and default config files."""
from __future__ import annotations

import logging
import pathlib

import yaml

_logger = logging.getLogger(__name__)

_DEFAULT_CONFIG: dict = {
    "contexts": {
        "local": {
            "path_kits": "$HOME/kits",
            "path_servers": "$HOME/kits",
            "path_secrets": "",
            "mode": "local",
        },
        "remote": {
            "path_kits": "$HOME/kits",
            "path_servers": "$HOME/kits",
            "path_secrets": "",
            "mode": "remote",
        },
    },
    "context": "local",
}

_DEFAULT_SERVERS: dict = {
    "servers": [
        {
            "name": "mariadb",
            "user": "root",
            "hosts": ["192.168.1.55", "10.0.0.234"],
            "port": "22",
            "password": "$PASSWORD",
            "pkey": "/home/user/.ssh/id_rsa",
        }
    ]
}

_DEFAULT_KITS: dict = {
    "kits": [
        "create-users/ikctl.yaml",
        "install-mariadb/ikctl.yaml",
    ]
}


class ConfigBootstrap:
    """Creates ~/.ikctl/ and ~/kits/ with default config files if they do not exist."""

    def __init__(
        self,
        home: pathlib.Path | None = None,
        interactive: bool = True,
    ) -> None:
        self._home = home or pathlib.Path.home()
        self._interactive = interactive
        self._ikctl_dir = self._home / ".ikctl"
        self._kits_dir = self._home / "kits"

    def setup(self) -> None:
        """Creates folders and default config files when missing."""
        self._ensure_ikctl_dir()
        self._ensure_kits_dir()
        self._ensure_config_file()
        self._ensure_kits_yaml()
        self._ensure_servers_yaml()

    def _ask(self, question: str) -> str:
        """Asks the user a yes/no question; returns 'yes' in non-interactive mode."""
        if not self._interactive:
            return "yes"
        return input(question)

    def _ensure_ikctl_dir(self) -> None:
        """Creates ~/.ikctl if it does not exist."""
        if not self._ikctl_dir.exists():
            answer = self._ask(
                "\nDo you want to create configuration files automatically? [yes, no]\n"
            )
            if answer == "yes":
                self._ikctl_dir.mkdir(parents=True, exist_ok=True)
                _logger.info("Created directory: %s", self._ikctl_dir)

    def _ensure_kits_dir(self) -> None:
        """Creates ~/kits if it does not exist."""
        if not self._kits_dir.exists():
            answer = self._ask(
                "\nDo you want to create configuration of servers and kits automatically? [yes, no]\n"
            )
            if answer == "yes":
                self._kits_dir.mkdir(parents=True, exist_ok=True)
                _logger.info("Created directory: %s", self._kits_dir)

    def _ensure_config_file(self) -> None:
        """Creates ~/.ikctl/config with defaults if it does not exist."""
        config_file = self._ikctl_dir / "config"
        if not config_file.exists() and self._ikctl_dir.exists():
            with open(config_file, "w", encoding="utf-8") as f:
                f.write(yaml.dump(_DEFAULT_CONFIG, default_flow_style=False))
            _logger.info("Created default config: %s", config_file)

    def _ensure_kits_yaml(self) -> None:
        """Creates ~/kits/ikctl.yaml with defaults if it does not exist."""
        kits_yaml = self._kits_dir / "ikctl.yaml"
        if not kits_yaml.exists() and self._kits_dir.exists():
            with open(kits_yaml, "w", encoding="utf-8") as f:
                f.write(yaml.dump(_DEFAULT_KITS, default_flow_style=False))
            _logger.info("Created default kits config: %s", kits_yaml)

    def _ensure_servers_yaml(self) -> None:
        """Creates ~/kits/config.yaml with defaults if it does not exist."""
        servers_yaml = self._kits_dir / "config.yaml"
        if not servers_yaml.exists() and self._kits_dir.exists():
            with open(servers_yaml, "w", encoding="utf-8") as f:
                f.write(yaml.dump(_DEFAULT_SERVERS, default_flow_style=False))
            _logger.info("Created default servers config: %s", servers_yaml)
