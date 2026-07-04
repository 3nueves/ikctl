"""Abstract base for SSH-like connections."""
from __future__ import annotations

from abc import ABC, abstractmethod

import paramiko


class IConnection(ABC):
    """Contract for SSH-like connections."""

    @abstractmethod
    def exec_command(self, command: str) -> tuple[str, str, int]:
        """Execute a command. Returns (stdout, stderr, exit_code)."""

    @abstractmethod
    def open_sftp(self) -> paramiko.SFTPClient:
        """Return an open SFTP client."""

    @abstractmethod
    def close(self) -> None:
        """Close all open channels and the connection."""
