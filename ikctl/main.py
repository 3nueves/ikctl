"""Module to load cli."""
from __future__ import annotations

import argparse
import logging
import os

from rich.console import Console
from rich.panel import Panel

from ikctl.config.config import Config, __version__
from ikctl.config.models import ServerGroup
from ikctl.connection.options import SSHOptions
from ikctl.connection.ssh import SSHConnection
from ikctl.executor.local import LocalExecutor
from ikctl.pipeline import Pipeline
from ikctl.runner.base import IRunner
from ikctl.runner.dry_run import DryRunRunner
from ikctl.runner.local import LocalRunner
from ikctl.runner.remote import RemoteRunner

_console = Console()


def _resolve_pipeline_path(pipeline_arg: str, path_pipelines: str | None) -> str:
    """Resolve the pipeline argument to an actual file path.

    Tries in order:
    1. If pipeline_arg is an existing file, return it directly.
    2. If path_pipelines is set, search <path_pipelines>/<pipeline_arg>[.yaml].
    3. Otherwise raise ConfigError with a clear message.
    """
    from ikctl.config.exceptions import ConfigError

    if os.path.isfile(pipeline_arg):
        return pipeline_arg

    if path_pipelines is not None:
        if pipeline_arg.endswith(".yaml") or pipeline_arg.endswith(".yml"):
            candidate = os.path.join(path_pipelines, pipeline_arg)
        else:
            candidate = os.path.join(path_pipelines, pipeline_arg + ".yaml")
        if os.path.isfile(candidate):
            return candidate

    raise ConfigError(
        f"Pipeline '{pipeline_arg}' not found. "
        "Provide an absolute path or set path_pipelines in ~/.ikctl/config"
    )


def _make_connection_factory(
    options: object,
    servers: ServerGroup,
    secrets: str,
    timeout_connect: float,
):
    """Return a connection factory for the given server group and options."""
    def connection_factory(host: str) -> SSHConnection:
        if servers.pkey:
            opts = SSHOptions(
                hostname=host,
                port=servers.port,
                username=servers.user,
                key_filename=servers.pkey,
                password=None,
                allow_agent=False,
                look_for_keys=False,
                timeout=timeout_connect,
            )
        elif servers.password != "no_pass":
            opts = SSHOptions(
                hostname=host,
                port=servers.port,
                username=servers.user,
                password=servers.password,
                key_filename=None,
                allow_agent=False,
                look_for_keys=False,
                timeout=timeout_connect,
            )
        else:
            opts = SSHOptions(
                hostname=host,
                port=servers.port,
                username=servers.user,
                password=secrets or None,
                key_filename=None,
                allow_agent=True,
                look_for_keys=True,
                timeout=timeout_connect,
            )
        return SSHConnection(opts)

    return connection_factory


def _build_runner(
    options: object,
    servers: ServerGroup,
    secrets: str,
    timeout_connect: float,
    timeout_exec: float,
) -> IRunner:
    """Construct and return the appropriate runner based on mode and flags."""
    if getattr(options, "dry_run", False):
        return DryRunRunner()

    mode = options.mode if hasattr(
        options, "mode") and options.mode else "remote"

    if mode == "local":
        executor = LocalExecutor(timeout=timeout_exec)
        return LocalRunner(executor)

    parallel_workers = getattr(options, "parallel_workers", 4) or 4
    return RemoteRunner(
        _make_connection_factory(options, servers, secrets, timeout_connect),
        max_workers=parallel_workers,
    )


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="tool for install software in remote and local machines",
        prog="ikctl",
    )
    parser.version = __version__
    parser.add_argument(
        "-l", "--list",
        choices=["kits", "servers", "context", "mode", "pipelines"],
        help="option to list kits, servers, context, mode or pipelines",
    )
    parser.add_argument("-i", "--install", help="Select kit to use")
    parser.add_argument("-n", "--name", help="Name of the groups servers")
    parser.add_argument("-p", "--parameter", nargs="*", help="Add parameters")
    parser.add_argument(
        "-s", "--sudo", choices=["sudo"], help="exec from sudo")
    parser.add_argument("-c", "--context", help="Select context")
    parser.add_argument(
        "-m", "--mode",
        choices=["local", "remote"],
        default="remote",
        help="Select mode",
    )
    parser.add_argument("-v", "--version", action="version")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview uploads and commands without executing anything",
    )
    parser.add_argument(
        "--timeout-connect",
        type=float,
        default=None,
        help="SSH connection timeout in seconds (default: 30.0)",
    )
    parser.add_argument(
        "--timeout-exec",
        type=float,
        default=None,
        help="Local command execution timeout in seconds (default: 120.0)",
    )
    parser.add_argument(
        "--parallel-workers",
        type=int,
        default=4,
        dest="parallel_workers",
        help="Maximum number of concurrent threads for parallel host execution (default: 4)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable verbose logging (paramiko and internal logs)",
    )
    parser.add_argument(
        "--pipeline",
        help="Path to a pipeline YAML file for DAG-based orchestration",
    )
    parser.add_argument(
        "--describe",
        help="Show kit manifest and declared outputs",
    )
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - [%(levelname)s] - %(message)s",
        )
    else:
        logging.basicConfig(level=logging.WARNING)
        logging.getLogger("paramiko").setLevel(logging.WARNING)
        logging.getLogger("paramiko.transport").setLevel(logging.WARNING)

    data = Config()
    config_servers, _ = data.load_config_file_servers()
    secrets, _ = data.extract_secrets()

    from ikctl.config.exceptions import ServerNotFoundError
    import sys

    try:
        servers_dict = data.extract_config_servers(config_servers, args.name)
    except ServerNotFoundError as exc:
        print(f"\nError: {exc}\n", file=sys.stderr)
        sys.exit(1)

    servers = ServerGroup(
        user=servers_dict["user"],
        port=servers_dict["port"],
        hosts=servers_dict["hosts"],
        password=servers_dict["password"],
        pkey=servers_dict.get("pkey"),
    )

    timeout_connect = args.timeout_connect if args.timeout_connect is not None else data.load_timeout_connect()
    timeout_exec = args.timeout_exec if args.timeout_exec is not None else data.load_timeout_exec()

    if args.pipeline:
        from ikctl.config.loader import ConfigLoader
        from ikctl.orchestration.parser import PipelineParser
        from ikctl.orchestration.runner import OrchestrationRunner

        try:
            from ikctl.config.exceptions import ConfigError
            loader = ConfigLoader(config_path=data.path_config_file)
            ikctl_config = loader.load()
            active_ctx = ikctl_config.contexts.get(ikctl_config.context)
            path_pipelines = active_ctx.path_pipelines if active_ctx else None
            resolved_pipeline = _resolve_pipeline_path(args.pipeline, path_pipelines)
        except ConfigError as exc:
            import sys
            print(f"\nError: {exc}\n", file=sys.stderr)
            sys.exit(1)
        except Exception as exc:
            import sys
            print(f"\nError loading config: {exc}\n", file=sys.stderr)
            sys.exit(1)

        pipeline_def = PipelineParser().parse(resolved_pipeline)
        mode = args.mode if hasattr(args, "mode") and args.mode else "remote"

        pipeline_params: dict[str, str] = {}
        if args.parameter:
            for item in args.parameter:
                if "=" in item:
                    key, _, value = item.partition("=")
                    pipeline_params[key.strip()] = value.strip()
                else:
                    logging.warning(
                        "Ignoring pipeline parameter '%s': not in KEY=VALUE format", item
                    )

        orch_runner = OrchestrationRunner(
            config=ikctl_config,
            connection_factory=_make_connection_factory(args, servers, secrets, timeout_connect),
            max_workers=getattr(args, "parallel_workers", 4) or 4,
            mode=mode,
            timeout_exec=timeout_exec,
        )

        _console.print(f"\n[bold cyan]Pipeline: {pipeline_def.name}[/bold cyan]\n")
        results = orch_runner.run(pipeline_def, args, pipeline_params=pipeline_params or None)

        for result in results:
            if result.status == "ok":
                _console.print(f"  [green]✓ {result.id:<20}[/green]  ok")
            elif result.status == "skipped":
                _console.print(f"  [yellow]⊘ {result.id:<20}[/yellow]  skipped")
            else:
                _console.print(f"  [red]✗ {result.id:<20}[/red]  failed")

        ok_count = sum(1 for r in results if r.status == "ok")
        failed_count = sum(1 for r in results if r.status == "failed")
        skipped_count = sum(1 for r in results if r.status == "skipped")
        color = "green" if failed_count == 0 else "red"
        summary = (
            f"[bold {color}]{ok_count} steps OK · {failed_count} FAILED · {skipped_count} SKIPPED"
            f"[/bold {color}]"
        )
        _console.print(Panel(summary, expand=False))

        import sys
        if any(r.status == "failed" for r in results):
            sys.exit(1)
        return

    if args.describe:
        import sys
        from ikctl.config.exceptions import KitNotFoundError
        from ikctl.config.loader import ConfigLoader
        from ikctl.config.kit_repo import KitRepository
        from ikctl.view import Show

        try:
            loader = ConfigLoader(config_path=data.path_config_file)
            ikctl_config = loader.load()
            repo = KitRepository(ikctl_config)
            kit_pipeline = repo.resolve(args.describe)
        except KitNotFoundError as exc:
            print(f"\nError: {exc}\n", file=sys.stderr)
            sys.exit(1)
        except Exception as exc:
            print(f"\nError loading kit: {exc}\n", file=sys.stderr)
            sys.exit(1)

        view = Show(
            kits=[],
            path_kits="",
            servers=[],
            path_servers="",
            contexts={},
            mode="",
            path_secrets="",
        )
        view.show_kit_describe(args.describe, kit_pipeline)
        return

    runner = _build_runner(args, servers, secrets, timeout_connect, timeout_exec)
    Pipeline(runner=runner, options=args)
