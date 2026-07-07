"""DryRunRunner: accumulates planned actions without executing them."""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path

from ikctl.config.models import KitPipeline, ServerGroup
from ikctl.runner.base import IRunner, RunOptions, RunResult
from ikctl.runner.utils import resolve_remote_dir


def _censor(command: str) -> str:
    """Replace plaintext passwords in echo pipes with ***."""
    return re.sub(r"echo\s+\S+\s*\|", "echo *** |", command)


def _build_preview_command(script_path: str, options: RunOptions) -> str:
    """Build the command preview string showing sudo and parameters."""
    script = os.path.basename(script_path)
    params = " ".join(options.parameter) if options.parameter else ""
    sudo = options.sudo

    if sudo and params:
        return f"echo *** | sudo -S bash {script} {params}"
    if sudo:
        return f"echo *** | sudo -S bash {script}"
    if params:
        return f"bash {script} {params}"
    return f"bash {script}"


class DryRunRunner(IRunner):
    """Runner that accumulates planned actions without executing them."""

    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)

    def run(self, kit: KitPipeline, servers: ServerGroup, options: RunOptions) -> list[RunResult]:
        """Return RunResults whose stdout contains the preview lines for each host."""
        results: list[RunResult] = []
        remote_dir = resolve_remote_dir(kit, options)
        for host in servers.hosts:
            lines = [f"\n[DRY RUN] Host: {host}"]
            for upload in kit.uploads:
                remote = f"{remote_dir}/{Path(upload).name}"
                lines.append(f"[DRY RUN] UPLOAD: {upload} → {remote}")
            for cmd in kit.pipeline:
                lines.append(
                    f"[DRY RUN] EXEC: {_censor(_build_preview_command(cmd, options))}")
            results.append(RunResult(host=host, success=True,
                           stdout="\n".join(lines), stderr=""))
        return results
