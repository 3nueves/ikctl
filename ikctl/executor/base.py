"""Abstract base for command executors."""
from __future__ import annotations

from abc import ABC, abstractmethod


class IExecutor(ABC):
    """Contract for executing shell commands."""

    @abstractmethod
    def execute(self, command: str) -> tuple[str, str, int]:
        """Execute a command. Returns (stdout, stderr, exit_code)."""
