"""DryRunRunner: accumulates planned actions without executing them."""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path

from ikctl.config.models import KitPipeline, ServerGroup
from ikctl.runner.base import IRunner
from ikctl.runner.result import RunResult


def _censor(command: str) -> str:
    """Replace plaintext passwords in echo pipes with ***."""
    return re.sub(r"echo\s+\S+\s*\|", "echo *** |", command)


def _build_preview_command(script_path: str, options: object) -> str:
    """Build the command preview string showing sudo and parameters."""
    script = os.path.basename(script_path)
    params = " ".join(options.parameter) if getattr(options, "parameter", None) else ""
    sudo = getattr(options, "sudo", None)

    if sudo and params:
        return f"echo *** | sudo -S bash {script} {params}"
    elif sudo:
        return f"echo *** | sudo -S bash {script}"
    elif params:
        return f"bash {script} {params}"
    else:
        return f"bash {script}"


class DryRunRunner(IRunner):
    """Runner that accumulates planned actions without executing them."""

    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)

    def run(self, kit: KitPipeline, servers: ServerGroup, options: object) -> list[RunResult]:
        """Return RunResults whose stdout contains the preview lines for each host."""
        results: list[RunResult] = []
        for host in servers.hosts:
            lines = [f"\n[DRY RUN] Host: {host}"]
            for upload in kit.uploads:
                remote = f".ikctl/{Path(upload).parent.name}/{Path(upload).name}"
                lines.append(f"[DRY RUN] UPLOAD: {upload} → {remote}")
            for cmd in kit.pipeline:
                lines.append(f"[DRY RUN] EXEC: {_censor(_build_preview_command(cmd, options))}")
            results.append(RunResult(host=host, success=True, stdout="\n".join(lines), stderr=""))
        return results
