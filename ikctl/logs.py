"""Logging utilities for displaying task results to stdout."""
from __future__ import annotations

from rich.console import Console

_console = Console()
_error_console = Console(stderr=True)


class Log:
    """Shows task stdout results with Rich colored output."""

    def stdout(
        self,
        logs: str | None = None,
        errors: str | None = None,
        check: int | None = None,
    ) -> None:
        """Prints colored Rich output for a completed task."""
        if check != 0:
            msg = errors if errors is not None else "End task with errors"
            _error_console.print(f"[bold red]{msg}[/bold red]")
        else:
            msg = logs if logs is not None else "End task successfully"
            _console.print(f"[bold green]{msg}[/bold green]")
