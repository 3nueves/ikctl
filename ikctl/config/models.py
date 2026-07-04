"""Data models for ikctl configuration."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ServerGroup:
    """Represents a group of servers with shared connection settings."""

    user: str
    port: int
    hosts: list[str]
    password: str | None = None
    pkey: str | None = None
    proxy_command: str | None = None
    host_key_policy: str = "auto_add"


@dataclass(frozen=True)
class KitPipeline:
    """Represents a kit with its upload list and pipeline steps."""

    uploads: list[str]
    pipeline: list[str]
    outputs: dict[str, str] = field(default_factory=dict)
    name: str = ""


@dataclass(frozen=True)
class Context:
    """Represents a named ikctl context."""

    name: str
    path_kits: str
    path_servers: str
    path_secrets: str
    mode: str
    timeout_connect: float = 30.0
    timeout_exec: float = 120.0
    exclude: list[str] = field(default_factory=list)
    kits_repo: str | None = None
    kits_ref: str = "main"
    kits_token: str | None = None
    path_pipelines: str | None = None
    path_remote_kits: str = "~/ikctl"


@dataclass(frozen=True)
class IkctlConfig:
    """Top-level ikctl configuration."""

    context: str
    contexts: dict[str, Context]
