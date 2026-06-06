"""Displays ikctl configuration to stdout."""
from __future__ import annotations

import pathlib

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ikctl.config.models import KitPipeline

_console = Console()


class Show:
    """Shows the app configuration for kits, servers and context."""

    def __init__(
        self,
        kits: list[str],
        path_kits: str,
        servers: list[dict],
        path_servers: str,
        contexts: dict,
        mode: str,
        path_secrets: str,
        path_pipelines: str | None = None,
        kit_pipelines: dict[str, KitPipeline] | None = None,
    ) -> None:
        self.kits = kits
        self.path_kits = path_kits
        self.servers = servers
        self.path_servers = path_servers
        self.contexts = contexts
        self.mode = mode
        self.path_secrets = path_secrets
        self._path_pipelines = path_pipelines
        self._kit_pipelines: dict[str, KitPipeline] = kit_pipelines or {}

    def show_config(self, conf: str) -> None:
        """Prints configuration for the given section (kits, servers, context, mode)."""
        if conf == "kits":
            table = Table(title="Kits", show_header=True)
            table.add_column("Kit", style="cyan")
            table.add_column("Outputs", style="dim")
            for kit_path in self.kits:
                kit_name = kit_path.replace("/ikctl.yaml", "")
                kit_pipeline = self._kit_pipelines.get(kit_name)
                if kit_pipeline and kit_pipeline.outputs:
                    outputs_str = ", ".join(kit_pipeline.outputs.keys())
                else:
                    outputs_str = "-"
                table.add_row(kit_name, outputs_str)
            _console.print(table)

        elif conf == "context":
            active_ctx = self.contexts.get("context", "")
            ctx_list = self.contexts.get("contexts", [])
            lines = []
            lines.append(f"Contexts: {', '.join(ctx_list)}")
            lines.append(f"Active context: {active_ctx}")
            lines.append(f"Mode: {self.mode}")
            lines.append(f"Path Kits: {self.path_kits}")
            lines.append(f"Path Servers: {self.path_servers}")
            lines.append(f"Path Secrets: {self.path_secrets}")
            _console.print(Panel("\n".join(lines), title="Context", border_style="blue"))

        elif conf == "mode":
            _console.print(f"Context: {self.contexts.get('context', '')}")

        elif conf == "servers" and self.mode != "local":
            table = Table(title="Servers", show_header=True)
            table.add_column("Name", style="cyan")
            table.add_column("User", style="green")
            table.add_column("Hosts")
            table.add_column("Port")
            table.add_column("Auth")
            for server in self.servers:
                name = str(server.get("name", ""))
                user = str(server.get("user", ""))
                hosts = ", ".join(server.get("hosts", [])) if isinstance(server.get("hosts"), list) else str(server.get("hosts", ""))
                port = str(server.get("port", ""))
                password = server.get("password", "")
                auth = "***" if password and password != "no_pass" else "key/agent"
                table.add_row(name, user, hosts, port, auth)
            _console.print(table)
        elif conf == "pipelines":
            if not self._path_pipelines:
                _console.print(
                    "[yellow]path_pipelines is not configured in the active context.[/yellow]"
                )
                _console.print(
                    "[dim]Add 'path_pipelines: ~/kits/pipelines' to ~/.ikctl/config[/dim]"
                )
                return
            path = pathlib.Path(self._path_pipelines)
            pipelines = sorted(path.glob("*.yaml")) if path.exists() else []
            if not pipelines:
                _console.print("[dim]No pipelines found in[/dim] " + str(path))
                return
            table = Table(title=f"Pipelines - {path}", show_header=True)
            table.add_column("Name", style="cyan")
            table.add_column("Path", style="dim")
            for p in pipelines:
                table.add_row(p.stem, str(p))
            _console.print(table)

        else:
            _console.print(f"You are in {self.mode} mode")

    def show_kit_describe(self, kit_name: str, kit: KitPipeline) -> None:
        """Show kit details: scripts and declared outputs."""
        uploads_table = Table(show_header=True, header_style="bold")
        uploads_table.add_column("Uploads")
        for u in kit.uploads:
            uploads_table.add_row(pathlib.Path(u).name)

        pipeline_table = Table(show_header=True, header_style="bold")
        pipeline_table.add_column("Pipeline")
        for p in kit.pipeline:
            pipeline_table.add_row(pathlib.Path(p).name)

        _console.print(Panel(f"[bold]{kit_name}[/bold]", title="Kit"))
        _console.print(uploads_table)
        _console.print(pipeline_table)

        if kit.outputs:
            outputs_table = Table(show_header=True, header_style="bold")
            outputs_table.add_column("Output Key", style="cyan")
            outputs_table.add_column("Description")
            for key, desc in kit.outputs.items():
                outputs_table.add_row(key, desc)
            _console.print(outputs_table)
        else:
            _console.print("[dim]No outputs declared[/dim]")
