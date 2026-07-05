"""SSH connection options dataclass."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ikctl.config.models import ServerGroup


@dataclass
class SSHOptions:
    """All options for an SSH connection."""

    hostname: str
    port: int = 22
    username: str | None = None
    password: str | None = None
    passphrase: str | None = None
    key_filename: str | None = None
    pkey: Any | None = None  # programmatic use only — never set by YAML or CLI
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

    @classmethod
    def from_server_group(
        cls,
        host: str,
        servers: ServerGroup,
        secrets: str,
        timeout: float,
    ) -> "SSHOptions":
        """Build SSHOptions selecting the right auth method from a ServerGroup.

        Priority:
        1. pkey defined  → publickey auth (password=None, allow_agent=False)
        2. password set  → password auth  (key_filename=None, allow_agent=False)
        3. none          → agent/key discovery (allow_agent=True, look_for_keys=True)
        """
        if servers.pkey:
            return cls(
                hostname=host,
                port=servers.port,
                username=servers.user,
                key_filename=servers.pkey,
                password=None,
                allow_agent=False,
                look_for_keys=False,
                timeout=timeout,
                proxy_command=servers.proxy_command,
                host_key_policy=servers.host_key_policy,
            )
        if servers.password is not None and servers.password != "no_pass":
            return cls(
                hostname=host,
                port=servers.port,
                username=servers.user,
                password=servers.password,
                key_filename=None,
                allow_agent=False,
                look_for_keys=False,
                timeout=timeout,
                proxy_command=servers.proxy_command,
                host_key_policy=servers.host_key_policy,
            )
        if servers.password == "no_pass":
            return cls(
                hostname=host,
                port=servers.port,
                username=servers.user,
                password=secrets or None,
                key_filename=None,
                allow_agent=False,
                look_for_keys=False,
                timeout=timeout,
                proxy_command=servers.proxy_command,
                host_key_policy=servers.host_key_policy,
            )
        return cls(
            hostname=host,
            port=servers.port,
            username=servers.user,
            password=secrets or None,
            key_filename=None,
            allow_agent=True,
            look_for_keys=True,
            timeout=timeout,
            proxy_command=servers.proxy_command,
            host_key_policy=servers.host_key_policy,
        )
