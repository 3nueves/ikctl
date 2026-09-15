"""Abstract base for SSH-like connections."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

import paramiko


class IConnection(ABC):
    """Contract for SSH-like connections."""

    @abstractmethod
    def exec_command(
        self,
        command: str,
        on_stdout: Callable[[str], None] | None = None,
        on_stderr: Callable[[str], None] | None = None,
    ) -> tuple[str, str, int]:
        """Execute a command. Returns (stdout, stderr, exit_code).

        When on_stdout/on_stderr callbacks are provided, they are invoked
        with each chunk of output as it arrives from the remote channel,
        before the command finishes.
        """

    @abstractmethod
    def open_sftp(self) -> paramiko.SFTPClient:
        """Return an open SFTP client."""

    @abstractmethod
    def close(self) -> None:
        """Close all open channels and the connection."""
