"""LocalExecutor: executes commands via subprocess."""
from __future__ import annotations

import logging
import re
import subprocess

from ikctl.executor.base import IExecutor


def _censor(command: str) -> str:
    """Redact passwords from sudo pipe patterns before logging."""
    return re.sub(r"echo\s+\S+\s*\|", "echo *** |", command)


class LocalExecutor(IExecutor):
    """Executes shell commands on the local machine using subprocess."""

    def __init__(self, timeout: float = 120.0) -> None:
        """Create a LocalExecutor with the given command timeout in seconds."""
        self._timeout = timeout
        self._logger = logging.getLogger(__name__)

    def execute(self, command: str) -> tuple[str, str, int]:
        """Execute a command locally. Returns (stdout, stderr, exit_code)."""
        self._logger.info("EXEC: %s", _censor(command))
        try:
            result = subprocess.run(
                command,
                shell=True,
                text=True,
                capture_output=True,
                timeout=self._timeout,
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            self._logger.warning("Command timed out after %s seconds: %s", self._timeout, _censor(command))
            return "", "Timeout expired", 1
