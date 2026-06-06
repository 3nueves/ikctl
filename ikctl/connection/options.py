"""SSH connection options dataclass."""
from __future__ import annotations

from dataclasses import dataclass

import paramiko


@dataclass
class SSHOptions:
    """All paramiko-relevant options for an SSH connection."""

    hostname: str
    port: int = 22
    username: str | None = None
    password: str | None = None
    passphrase: str | None = None
    key_filename: str | list[str] | None = None
    pkey: paramiko.PKey | None = None
    allow_agent: bool = True
    look_for_keys: bool = True
    timeout: float = 30.0
    auth_timeout: float = 30.0
    banner_timeout: float = 30.0
    channel_timeout: float | None = None
    keepalive_interval: int = 0
    compress: bool = False
    disabled_algorithms: dict | None = None
    host_key_policy: str = "auto_add"
    proxy_command: str | None = None
