"""RunResult dataclass representing the outcome of a kit execution on a host."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RunResult:
    """Result of running a kit against a single host."""

    host: str
    success: bool
    stdout: str
    stderr: str
