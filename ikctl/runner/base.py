"""Abstract base for kit runners."""
from __future__ import annotations

from abc import ABC, abstractmethod

from ikctl.config.models import KitPipeline, ServerGroup
from ikctl.runner.result import RunResult


class IRunner(ABC):
    """Contract for running a kit against a set of servers."""

    @abstractmethod
    def run(self, kit: KitPipeline, servers: ServerGroup, options: object) -> list[RunResult]:
        """Execute the kit on the given servers. Returns one RunResult per host."""
