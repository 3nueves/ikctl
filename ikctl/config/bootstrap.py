"""Creates the initial ~/.ikctl/ folder structure and default config files."""
from __future__ import annotations

import logging
import pathlib

import yaml

_logger = logging.getLogger(__name__)

_DEFAULT_SERVERS: dict = {
    "servers": [
        {
            "name": "mariadb",
            "user": "root",
            "hosts": ["192.168.1.55", "10.0.0.234"],
            "port": "22",
            "pkey": "/home/user/.ssh/id_rsa",
        }
    ]
}

_DEFAULT_CONFIG: str = """\
# Active context used by default
context: local

contexts:
  local:
    # Execution mode: "local" runs commands on this machine, "remote" via SSH
    mode: local
    # Directory where kits are stored
    path_kits: {kits_path}
    # Directory where servers config.yaml is located
    path_servers: {servers_path}
    # Path to the .secrets file (env vars injected at runtime)
    path_secrets: {servers_path}/.secrets
    # Directory where pipeline .yaml files are located
    path_pipelines: {pipelines_path}
    # Seconds to wait when opening an SSH connection
    # timeout_connect: 30.0
    # Seconds to wait for a remote command to finish
    # timeout_exec: 120.0
    # Kits to exclude from discovery
    # exclude: []
    # Git repo URL to pull kits from automatically
    # kits_repo: https://github.com/org/kits.git
    # Branch or tag to checkout from kits_repo
    # kits_ref: main
    # Token for private kits_repo
    # kits_token: ghp_xxxx

  remote:
    # Execution mode: "local" runs commands on this machine, "remote" via SSH
    mode: remote
    # Directory where kits are stored
    path_kits: {kits_path}
    # Directory where servers config.yaml is located
    path_servers: {servers_path}
    # Path to the .secrets file (env vars injected at runtime)
    path_secrets: {servers_path}/.secrets
    # Directory where pipeline .yaml files are located
    path_pipelines: {pipelines_path}
    # Seconds to wait when opening an SSH connection
    # timeout_connect: 30.0
    # Seconds to wait for a remote command to finish
    # timeout_exec: 120.0
    # Kits to exclude from discovery
    # exclude: []
    # Git repo URL to pull kits from automatically
    # kits_repo: https://github.com/org/kits.git
    # Branch or tag to checkout from kits_repo
    # kits_ref: main
    # Token for private kits_repo
    # kits_token: ghp_xxxx
"""

_EXAMPLE_KIT: str = """\
kits:
  uploads:
    - date.sh
  pipeline:
    - date.sh
"""

_EXAMPLE_PIPELINE: str = """\
name: example
steps:
  - id: show-date
    kit: example-kit
    servers: mariadb
"""


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
        self._default_dir = self._home / "kits" / "default"
        self._kits_dir = self._default_dir / "kits"
        self._pipelines_dir = self._default_dir / "pipelines"
        self._servers_dir = self._default_dir / "servers"

    def setup(self) -> None:
        """Creates folders and default config files when missing."""
        if not self._needs_setup():
            return
        if not self._confirm():
            return
        self._ensure_ikctl_dir()
        self._ensure_default_dirs()
        self._ensure_config_file()
        self._ensure_servers_yaml()
        self._ensure_secrets_file()
        self._ensure_example_kit()
        self._ensure_example_pipeline()

    def _needs_setup(self) -> bool:
        """Returns True only when ikctl has never been configured (no config file exists)."""
        return not (self._ikctl_dir / "config").exists()

    def _confirm(self) -> bool:
        """Asks once for confirmation; always returns True in non-interactive mode."""
        if not self._interactive:
            return True
        answer = input(
            "\nDo you want to create configuration files automatically? [yes, no]\n")
        return answer == "yes"

    def _ensure_ikctl_dir(self) -> None:
        """Creates ~/.ikctl if it does not exist."""
        if not self._ikctl_dir.exists():
            self._ikctl_dir.mkdir(parents=True, exist_ok=True)
            _logger.info("Created directory: %s", self._ikctl_dir)

    def _ensure_default_dirs(self) -> None:
        """Creates ~/kits/default/{kits,pipelines,servers} if they do not exist."""
        for subdir in (self._kits_dir, self._pipelines_dir, self._servers_dir):
            if not subdir.exists():
                subdir.mkdir(parents=True, exist_ok=True)
                _logger.info("Created directory: %s", subdir)

    def _ensure_config_file(self) -> None:
        """Creates ~/.ikctl/config with defaults if it does not exist."""
        config_file = self._ikctl_dir / "config"
        if config_file.exists() or not self._ikctl_dir.exists():
            return
        content = _DEFAULT_CONFIG.format(
            kits_path=str(self._kits_dir),
            servers_path=str(self._servers_dir),
            pipelines_path=str(self._pipelines_dir),
        )
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(content)
        _logger.info("Created default config: %s", config_file)

    def _ensure_servers_yaml(self) -> None:
        """Creates ~/kits/default/servers/config.yaml with defaults if it does not exist."""
        servers_yaml = self._servers_dir / "config.yaml"
        if servers_yaml.exists() or not self._servers_dir.exists():
            return
        with open(servers_yaml, "w", encoding="utf-8") as f:
            f.write(yaml.dump(_DEFAULT_SERVERS, default_flow_style=False))
        _logger.info("Created default servers config: %s", servers_yaml)

    def _ensure_secrets_file(self) -> None:
        """Creates ~/kits/default/servers/.secrets (empty) if it does not exist."""
        secrets_file = self._servers_dir / ".secrets"
        if secrets_file.exists() or not self._servers_dir.exists():
            return
        with open(secrets_file, "w", encoding="utf-8") as f:
            f.write("")
        _logger.info("Created secrets file: %s", secrets_file)

    def _ensure_example_kit(self) -> None:
        """Creates ~/kits/default/kits/example-kit/ikctl.yaml if it does not exist."""
        kit_dir = self._kits_dir / "example-kit"
        kit_file = kit_dir / "ikctl.yaml"
        if kit_file.exists():
            return
        if not self._kits_dir.exists():
            return
        kit_dir.mkdir(parents=True, exist_ok=True)
        with open(kit_file, "w", encoding="utf-8") as f:
            f.write(_EXAMPLE_KIT)
        _logger.info("Created example kit: %s", kit_file)

    def _ensure_example_pipeline(self) -> None:
        """Creates ~/kits/default/pipelines/example.yaml if it does not exist."""
        pipeline_file = self._pipelines_dir / "example.yaml"
        if pipeline_file.exists() or not self._pipelines_dir.exists():
            return
        with open(pipeline_file, "w", encoding="utf-8") as f:
            f.write(_EXAMPLE_PIPELINE)
        _logger.info("Created example pipeline: %s", pipeline_file)
