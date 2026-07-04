"""Onboarding wizard for ikctl --init."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from ikctl.init.scaffold import Scaffold, ScaffoldPaths

_console = Console()


class InitWizard:
    """Orchestrates the creation of the ikctl configuration artefacts."""

    def __init__(
        self,
        base: Path | None = None,
        auto: bool = False,
        force: bool = False,
    ) -> None:
        """
        base: root directory for tests (default: Path.home()).
        auto: if True, skip confirmation prompts.
        force: if True, overwrite existing files.
        """
        _base = base if base is not None else Path.home()
        self._auto = auto
        paths = ScaffoldPaths.default(
            _base) if auto else self._ask_paths(_base)
        self._scaffold = Scaffold(paths, force=force)

    def _ask_paths(self, base: Path) -> ScaffoldPaths:
        """Ask the user ruta a ruta whether they want to change each default path.

        For each path: show label + default, ask [s/n], if 's' prompt for new value.
        Prints a summary of all chosen paths at the end.
        Returns a ScaffoldPaths built from the chosen paths.
        """
        defaults = ScaffoldPaths.default(base)

        def _ask_one(label: str, default: Path) -> Path:
            try:
                change = input(
                    f"\n  ¿Cambiar ruta de {label}?\n  Default: {default}\n  [s/n]: ").strip().lower()
            except EOFError:
                change = "n"
            if change == "s":
                try:
                    raw = input(f"  Nueva ruta: ").strip()
                except EOFError:
                    raw = ""
                return Path(raw) if raw else default
            return default

        _console.print("\n[bold cyan]Configuración de rutas[/bold cyan]")
        _console.print(f"  Config file    : {defaults.config_file} [fija]")
        servers_file = _ask_one("Servers file", defaults.servers_file)
        kits_dir = _ask_one("Kits directory", defaults.kits_dir)
        pipelines_dir = _ask_one("Pipelines directory", defaults.pipelines_dir)

        paths = ScaffoldPaths(
            config_file=defaults.config_file,
            servers_file=servers_file,
            secrets_file=servers_file.parent / ".secrets",
            kits_dir=kits_dir,
            pipelines_dir=pipelines_dir,
        )

        _console.print("\n[bold]Resumen de rutas:[/bold]")
        _console.print(f"  Config file    : {paths.config_file}")
        _console.print(f"  Servers file   : {paths.servers_file}")
        _console.print(f"  Kits directory : {paths.kits_dir}")
        _console.print(f"  Pipelines dir  : {paths.pipelines_dir}")

        return paths

    def _step(
        self,
        n: int,
        title: str,
        description: str,
        create_fn: Callable[[], list[Path]],
    ) -> list[Path]:
        """Display step header and run create_fn.

        In interactive mode, asks for confirmation before proceeding.
        Returns list of paths created (may be empty if skipped).
        """
        _console.print(
            f"\n[bold cyan]Step {n}:[/bold cyan] [bold]{title}[/bold]")
        _console.print(f"  {description}")

        if not self._auto:
            try:
                answer = input(
                    "  [Enter to continue / s to skip]: ").strip().lower()
            except EOFError:
                answer = ""
            if answer == "s":
                _console.print("  [yellow]skipped by user[/yellow]")
                return []

        return create_fn()

    def _create_config(self) -> list[Path]:
        """Generate ~/.ikctl/config."""
        p = self._scaffold.paths
        return [p.config_file] if self._scaffold.create_config() else []

    def _create_servers(self) -> list[Path]:
        """Generate servers/config.yaml and .secrets."""
        p = self._scaffold.paths
        created: list[Path] = []
        if self._scaffold.create_servers():
            created.append(p.servers_file)
        if self._scaffold.create_secrets():
            created.append(p.secrets_file)
        return created

    def _create_kit(self) -> list[Path]:
        """Generate example-kit/ikctl.yaml and date.sh."""
        return self._scaffold.create_example_kit()

    def _create_pipeline(self) -> list[Path]:
        """Generate pipelines/example.yaml."""
        p = self._scaffold.paths
        pipeline_file = p.pipelines_dir / "example.yaml"
        return [pipeline_file] if self._scaffold.create_example_pipeline() else []

    def _print_summary(self, created: list[Path]) -> None:
        """Print a Rich panel with created files and suggested commands."""
        lines: list[str] = ["[bold]ikctl init completed[/bold]", ""]
        if created:
            lines.append("Files created:")
            for path in created:
                lines.append(f"  [green]v[/green] {path}")
        else:
            lines.append(
                "[yellow]No new files created (all already existed).[/yellow]")
        lines += [
            "",
            "Test your installation:",
            "  ikctl --list kits",
            "  ikctl --install example-kit",
            "  ikctl --install example-kit --mode local",
            "  ikctl --pipeline example",
        ]
        _console.print(Panel("\n".join(lines), expand=False))

    def run(self) -> list[Path]:
        """Execute the 4 setup steps and print the summary panel.

        Returns a list of all paths that were actually created.
        """
        created: list[Path] = []
        p = self._scaffold.paths

        created += self._step(
            1,
            "Main configuration",
            f"Creates {p.config_file} with 'local' and 'remote' contexts.",
            self._create_config,
        )
        created += self._step(
            2,
            "Server definitions",
            f"Creates {p.servers_file} with a default server group and .secrets file.",
            self._create_servers,
        )
        created += self._step(
            3,
            "Example kit",
            f"Creates {p.kits_dir / 'example-kit'} with a manifest and a date.sh script.",
            self._create_kit,
        )
        created += self._step(
            4,
            "Example pipeline",
            f"Creates {p.pipelines_dir / 'example.yaml'} with a single 'show-date' step.",
            self._create_pipeline,
        )

        self._print_summary(created)
        return created
