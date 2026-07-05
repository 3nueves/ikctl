"""LocalRunner: orchestrates kit execution on the local machine."""
from __future__ import annotations

import logging
import os

from ikctl.executor.interface import IExecutor
from ikctl.runner.base import IRunner, RunOptions, RunResult
from ikctl.config.models import KitPipeline, ServerGroup


def _build_local_command(script_path: str, options: RunOptions, password: str) -> str:
    """Build the local bash command with optional sudo and parameters."""
    directory = os.path.dirname(script_path)
    script = os.path.basename(script_path)
    params = " ".join(options.parameter) if options.parameter else ""
    sudo = options.sudo

    if sudo and params:
        return f"cd {directory}; echo {password or ''} | sudo -S bash {script} {params}"
    if sudo:
        return f"cd {directory}; echo {password or ''} | sudo -S bash {script}"
    if params:
        return f"cd {directory}; bash {script} {params}"
    return f"cd {directory}; bash {script}"


class LocalRunner(IRunner):
    """Runs a kit locally using the provided executor."""

    def __init__(self, executor: IExecutor) -> None:
        """Create a LocalRunner backed by the given executor."""
        self._executor = executor
        self._logger = logging.getLogger(__name__)

    def run(self, kit: KitPipeline, servers: ServerGroup, options: RunOptions) -> list[RunResult]:
        """Execute the kit pipeline locally. Returns a single RunResult with host='local'."""
        self._logger.info("Starting local execution")

        all_stdout: list[str] = []
        all_stderr: list[str] = []
        success = True

        password = options.sudo_password if options.sudo_password else (
            servers.password if hasattr(servers, "password") else None)
        for cmd in kit.pipeline:
            full_cmd = _build_local_command(cmd, options, password)
            stdout, stderr, exit_code = self._executor.execute(full_cmd)
            all_stdout.append(stdout)
            all_stderr.append(stderr)
            if exit_code != 0:
                success = False
                self._logger.error(
                    "Step failed (exit %d): %s", exit_code, stderr)
                break

        return [RunResult(
            host="local",
            success=success,
            stdout="\n".join(all_stdout),
            stderr="\n".join(all_stderr),
        )]
