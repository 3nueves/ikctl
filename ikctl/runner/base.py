"""Abstract base for kit runners."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ikctl.config.models import KitPipeline, ServerGroup


def resolve_sudo_password(servers: ServerGroup, secrets: str) -> str:
    """Resolve the actual sudo password from servers config + secrets.

    When servers.password == 'no_pass', the real password lives in the .secrets file.
    Otherwise, servers.password holds the real password directly.
    """
    if servers.password == "no_pass":
        return secrets or ""
    return servers.password or ""


@dataclass
class RunOptions:
    """Generic options for kit execution. Can be extended with custom fields as needed."""
    parameter: list[str] | None = None
    sudo: bool = False
    install: str | None = None
    name: str | None = None
    mode: str | None = None
    parallel_workers: int | None = None
    dry_run: bool = False
    debug: bool = False
    stdout_output: bool = False
    stderr_output: bool = False
    context: str | None = None
    list: str | None = None
    strict: bool = False


@dataclass
class RunResult:
    """Result of running a kit against a single host."""

    host: str
    success: bool
    stdout: str
    stderr: str


class IRunner(ABC):
    """Contract for running a kit against a set of servers."""

    @abstractmethod
    def run(self, kit: KitPipeline, servers: ServerGroup, options: RunOptions) -> list[RunResult]:
        """Execute the kit on the given servers. Returns one RunResult per host."""
