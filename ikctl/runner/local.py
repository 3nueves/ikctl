"""LocalRunner: orchestrates kit execution on the local machine."""
from __future__ import annotations

import logging
import os

from ikctl.config.models import KitPipeline, ServerGroup


def _build_local_command(script_path: str, options: object, password: str) -> str:
    """Build the local bash command with optional sudo and parameters."""
    directory = os.path.dirname(script_path)
    script = os.path.basename(script_path)
    params = " ".join(options.parameter) if getattr(options, "parameter", None) else ""
    sudo = getattr(options, "sudo", None)

    if sudo and params:
        return f"cd {directory}; echo {password} | sudo -S bash {script} {params}"
    elif sudo:
        return f"cd {directory}; echo {password} | sudo -S bash {script}"
    elif params:
        return f"cd {directory}; bash {script} {params}"
    else:
        return f"cd {directory}; bash {script}"
from ikctl.executor.base import IExecutor
from ikctl.runner.base import IRunner
from ikctl.runner.result import RunResult


class LocalRunner(IRunner):
    """Runs a kit locally using the provided executor."""

    def __init__(self, executor: IExecutor) -> None:
        """Create a LocalRunner backed by the given executor."""
        self._executor = executor
        self._logger = logging.getLogger(__name__)

    def run(self, kit: KitPipeline, servers: ServerGroup, options: object) -> list[RunResult]:
        """Execute the kit pipeline locally. Returns a single RunResult with host='local'."""
        self._logger.info("Starting local execution")

        all_stdout: list[str] = []
        all_stderr: list[str] = []
        success = True

        password = servers.password if hasattr(servers, "password") else "no_pass"
        for cmd in kit.pipeline:
            full_cmd = _build_local_command(cmd, options, password)
            stdout, stderr, exit_code = self._executor.execute(full_cmd)
            all_stdout.append(stdout)
            all_stderr.append(stderr)
            if exit_code != 0:
                success = False
                self._logger.error("Step failed (exit %d): %s", exit_code, stderr)
                break

        return [RunResult(
            host="local",
            success=success,
            stdout="\n".join(all_stdout),
            stderr="\n".join(all_stderr),
        )]
