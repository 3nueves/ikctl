"""Shared runner utilities."""
from __future__ import annotations

from ikctl.config.models import KitPipeline
from ikctl.runner.base import RunOptions


def resolve_remote_dir(kit: KitPipeline, options: RunOptions) -> str:
    """Resolve remote upload directory: CLI > ikctl.yaml > .ikctl/<kit.name>/."""
    if options.remote_dir:
        return options.remote_dir
    if kit.remote_dir:
        return kit.remote_dir
    return f".ikctl/{kit.name}"