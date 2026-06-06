"""RemoteExecutor: executes commands via an IConnection."""
from __future__ import annotations

import logging
import re

from ikctl.connection.base import IConnection
from ikctl.executor.base import IExecutor


def _censor(command: str) -> str:
    """Redact passwords from sudo pipe patterns before logging."""
    return re.sub(r"echo\s+\S+\s*\|", "echo *** |", command)


class RemoteExecutor(IExecutor):
    """Executes shell commands on a remote host via an IConnection."""

    def __init__(self, connection: IConnection) -> None:
        """Create a RemoteExecutor backed by the given connection."""
        self._connection = connection
        self._logger = logging.getLogger(__name__)

    def execute(self, command: str) -> tuple[str, str, int]:
        """Execute a command remotely. Returns (stdout, stderr, exit_code)."""
        self._logger.info("EXEC: %s", _censor(command))
        stdout, stderr, exit_code = self._connection.exec_command(command)
        return stdout, stderr, exit_code
