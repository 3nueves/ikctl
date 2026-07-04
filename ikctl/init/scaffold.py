"""Pure file-creation logic for ikctl installation — no UI, no prompts."""
from __future__ import annotations

import pathlib
from dataclasses import dataclass

# ── Templates ─────────────────────────────────────────────────────────────────

# From bootstrap.py: full two-context config with inline comments.
_CONFIG_TEMPLATE: str = """\
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

# From bootstrap.py: same data as _DEFAULT_SERVERS dict, written as YAML string
# to avoid importing yaml in this module.
_SERVERS_TEMPLATE: str = """\
servers:
  - name: mariadb
    user: root
    port: "22"
    pkey: /home/user/.ssh/id_rsa
    hosts:
      - 192.168.1.55
      - 10.0.0.234
"""

# From wizard.py
_KIT_MANIFEST_TEMPLATE: str = """\
kits:
  uploads:
    - date.sh
  pipeline:
    - date.sh
"""

# From wizard.py
_KIT_SCRIPT_TEMPLATE: str = """\
#!/bin/bash
echo "DATE=$(date)"
"""

# From wizard.py
_PIPELINE_TEMPLATE: str = """\
name: example
steps:
  - id: show-date
    kit: show-date
    servers: mariadb
"""

# ── Paths ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ScaffoldPaths:
    """Canonical installation paths for ikctl — single source of truth."""

    config_file: pathlib.Path
    servers_file: pathlib.Path
    secrets_file: pathlib.Path
    kits_dir: pathlib.Path
    pipelines_dir: pathlib.Path

    @classmethod
    def default(cls, home: pathlib.Path | None = None) -> "ScaffoldPaths":
        """Return paths rooted at *home* (defaults to Path.home())."""
        h = home or pathlib.Path.home()
        default_dir = h / "kits" / "default"
        return cls(
            config_file=h / ".ikctl" / "config",
            servers_file=default_dir / "servers" / "config.yaml",
            secrets_file=default_dir / "servers" / ".secrets",
            kits_dir=default_dir / "kits",
            pipelines_dir=default_dir / "pipelines",
        )


# ── Core helper ────────────────────────────────────────────────────────────────


def write_if_absent(path: pathlib.Path, content: str, force: bool = False) -> bool:
    """Write *content* to *path* only when the file does not already exist (or force=True).

    Creates parent directories as needed.
    Returns True if the file was written, False if it already existed and force=False.
    """
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


# ── Scaffold ───────────────────────────────────────────────────────────────────


class Scaffold:
    """Creates the ikctl file structure without any UI or prompts.

    Used by both ConfigBootstrap (silent) and InitWizard (interactive).
    """

    def __init__(self, paths: ScaffoldPaths, force: bool = False) -> None:
        self._p = paths
        self._force = force

    @property
    def paths(self) -> ScaffoldPaths:
        return self._p

    def create_config(self) -> bool:
        """Write ~/.ikctl/config. Returns True if created."""
        p = self._p
        content = _CONFIG_TEMPLATE.format(
            kits_path=str(p.kits_dir),
            servers_path=str(p.servers_file.parent),
            pipelines_path=str(p.pipelines_dir),
        )
        return write_if_absent(p.config_file, content, self._force)

    def create_servers(self) -> bool:
        """Write servers/config.yaml. Returns True if created."""
        return write_if_absent(self._p.servers_file, _SERVERS_TEMPLATE, self._force)

    def create_secrets(self) -> bool:
        """Write empty .secrets file. Returns True if created."""
        return write_if_absent(self._p.secrets_file, "", self._force)

    def create_example_kit(self) -> list[pathlib.Path]:
        """Write example-kit/ikctl.yaml and date.sh. Returns list of created paths."""
        kit_dir = self._p.kits_dir / "example-kit"
        created: list[pathlib.Path] = []
        manifest = kit_dir / "ikctl.yaml"
        script = kit_dir / "date.sh"
        if write_if_absent(manifest, _KIT_MANIFEST_TEMPLATE, self._force):
            created.append(manifest)
        if write_if_absent(script, _KIT_SCRIPT_TEMPLATE, self._force):
            created.append(script)
        return created

    def create_example_pipeline(self) -> bool:
        """Write pipelines/example.yaml. Returns True if created."""
        return write_if_absent(self._p.pipelines_dir / "example.yaml", _PIPELINE_TEMPLATE, self._force)

    def create_all(self) -> list[pathlib.Path]:
        """Run all creation steps. Returns list of paths actually written."""
        created: list[pathlib.Path] = []
        if self.create_config():
            created.append(self._p.config_file)
        if self.create_servers():
            created.append(self._p.servers_file)
        if self.create_secrets():
            created.append(self._p.secrets_file)
        created.extend(self.create_example_kit())
        pipeline = self._p.pipelines_dir / "example.yaml"
        if self.create_example_pipeline():
            created.append(pipeline)
        return created
