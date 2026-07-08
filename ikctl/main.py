"""Module to load cli."""
from __future__ import annotations

import argparse
import logging
import pathlib
import sys

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel

from ikctl.config.config import Config, __version__
from ikctl.exceptions import ConfigError, KitNotFoundError, RunnerError, ServerNotFoundError
from ikctl.config.kit_repo import KitRepository
from ikctl.config.loader import ConfigLoader
from ikctl.config.models import ServerGroup
from ikctl.connection.models import SSHOptions
from ikctl.connection.ssh import SSHConnection
from ikctl.executor.local import LocalExecutor
from ikctl.init.wizard import InitWizard
from ikctl.orchestration.parser import PipelineParser
from ikctl.orchestration.runner import OrchestrationRunner
from ikctl.pipeline import Pipeline
from ikctl.runner.base import IRunner, RunOptions
from ikctl.runner.dry_run import DryRunRunner
from ikctl.runner.local import LocalRunner
from ikctl.runner.remote import RemoteRunner, _console as _runner_console
from ikctl.view import Show

_console = Console()


def _resolve_pipeline_path(pipeline_arg: str, path_pipelines: str | None) -> str:
    """Resolve the pipeline argument to an actual file path.

    Tries in order:
    1. If pipeline_arg is an existing file, return it directly.
    2. If path_pipelines is set, search <path_pipelines>/<pipeline_arg>[.yaml].
    3. Otherwise raise ConfigError with a clear message.
    """
    if pathlib.Path(pipeline_arg).is_file():
        return pipeline_arg

    if path_pipelines is not None:
        name = pipeline_arg if pipeline_arg.endswith(
            (".yaml", ".yml")) else pipeline_arg + ".yaml"
        candidate = pathlib.Path(path_pipelines) / name
        if candidate.is_file():
            return str(candidate)

    raise ConfigError(
        f"Pipeline '{pipeline_arg}' not found. "
        "Provide an absolute path or set path_pipelines in ~/.ikctl/config"
    )


def _make_connection_factory(
    servers: ServerGroup,
    secrets: str,
    timeout_connect: float,
):
    """Return a connection factory for the given server group and options."""
    def connection_factory(host: str) -> SSHConnection:
        opts = SSHOptions.from_server_group(
            host, servers, secrets, timeout_connect)
        return SSHConnection(opts)

    return connection_factory


def _build_runner(
    options: RunOptions,
    servers: ServerGroup,
    secrets: str,
    timeout_connect: float,
    timeout_exec: float,
    config_mode: str | None = "remote",
) -> IRunner:
    """Construct and return the appropriate runner based on mode and flags."""

    if options.dry_run:
        return DryRunRunner()

    mode = options.mode or config_mode

    if mode == "local":
        executor = LocalExecutor(timeout=timeout_exec)
        return LocalRunner(executor)

    parallel_workers = options.parallel_workers or 4
    return RemoteRunner(
        _make_connection_factory(servers, secrets, timeout_connect),
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
    parser.add_argument("-p", "--parameter", action="append", default=[], help="Add parameters (-p KEY=VALUE, repeatable)")
    parser.add_argument(
        "-s", "--sudo", choices=["sudo"], help="exec from sudo")
    parser.add_argument("-c", "--context", help="Select context")
    parser.add_argument(
        "-m", "--mode",
        choices=["local", "remote"],
        default=None,
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
        "--stdout",
        action="store_true",
        default=False,
        help="Show script stdout output",
    )
    parser.add_argument(
        "--stderr",
        action="store_true",
        default=False,
        help="Show script stderr output on failure",
    )
    parser.add_argument(
        "--pipeline",
        help="Path to a pipeline YAML file for DAG-based orchestration",
    )
    parser.add_argument(
        "--describe",
        help="Show kit manifest and declared outputs",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        default=False,
        help="Interactive onboarding wizard — creates config, servers, kit and pipeline examples",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        default=False,
        help="Used with --init: skip confirmation prompts (non-interactive mode)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Used with --init: overwrite existing files",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Run scripts with bash -eo pipefail (fail on any command error or pipe failure)",
    )
    parser.add_argument(
        "--sudo-password",
        default=None,
        help="Password for sudo (falls back to .secrets, then servers.password)",
    )
    parser.add_argument(
        "--force-upload",
        action="store_true",
        default=False,
        help="Upload all files even if unchanged (skip SHA256 verification)",
    )
    parser.add_argument(
        "--remote-dir",
        type=str,
        default=None,
        dest="remote_dir",
        help="Remote directory for uploads (overrides kit's remote_dir in ikctl.yaml)",
    )
    parser.add_argument(
        "--host",
        action="append",
        default=None,
        dest="host",
        help="Remote host (repeatable). When used, --user/--password/--port/--key replace servers/config.yaml",
    )
    parser.add_argument(
        "--user",
        default="root",
        help="SSH user (default: root, only with --host)",
    )
    parser.add_argument(
        "--password",
        default=None,
        help="SSH password (only with --host)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=22,
        help="SSH port (default: 22, only with --host)",
    )
    parser.add_argument(
        "--key",
        default=None,
        help="Path to SSH private key (only with --host)",
    )
    args = parser.parse_args()

    _actionable = (args.install, args.pipeline, args.describe,
                   args.list, args.context, args.init)
    if not any(_actionable):
        parser.print_help()
        sys.exit(0)

    if args.init:
        wizard = InitWizard(auto=args.auto, force=args.force)
        wizard.run()
        sys.exit(0)

    if args.debug:
        logging.basicConfig(
            level=logging.INFO,
            format="%(name)s - %(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(
                console=_runner_console,
                rich_tracebacks=False,
                show_path=False,
                show_time=True,
            )],
        )
    else:
        logging.basicConfig(level=logging.WARNING)
        logging.getLogger("paramiko").setLevel(logging.WARNING)
        logging.getLogger("paramiko.transport").setLevel(logging.WARNING)

    data = Config()

    if args.host:
        servers = ServerGroup(
            user=args.user,
            port=args.port,
            hosts=args.host,
            password=args.password or None,
            pkey=args.key or None,
        )
        secrets = None
        config_mode = "remote"
        timeout_connect = args.timeout_connect if args.timeout_connect is not None else 30.0
        timeout_exec = args.timeout_exec if args.timeout_exec is not None else 120.0
        sudo_password = args.sudo_password or args.password or None
    else:
        try:
            config_servers, _ = data.load_config_file_servers()
        except ConfigError as exc:
            print(f"\nError: {exc}\n", file=sys.stderr)
            sys.exit(1)
        secrets, _ = data.extract_secrets()
        config_mode = data.load_config_file_mode()

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

        sudo_password = args.sudo_password
        if not sudo_password:
            sudo_password = secrets or None
        if not sudo_password:
            sudo_password = servers_dict.get("password") or None

    if args.pipeline:
        try:
            loader = ConfigLoader(config_path=data.path_config_file)
            ikctl_config = loader.load()
            active_ctx = ikctl_config.contexts.get(ikctl_config.context)
            path_pipelines = active_ctx.path_pipelines if active_ctx else None
            resolved_pipeline = _resolve_pipeline_path(
                args.pipeline, path_pipelines)
        except ConfigError as exc:
            print(f"\nError: {exc}\n", file=sys.stderr)
            sys.exit(1)

        pipeline_def = PipelineParser().parse(resolved_pipeline)
        mode = args.mode if hasattr(args, "mode") and args.mode else config_mode

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
            connection_factory=_make_connection_factory(
                servers, secrets, timeout_connect),
            max_workers=getattr(args, "parallel_workers", 4) or 4,
            mode=mode,
            timeout_exec=timeout_exec,
            sudo_password=sudo_password,
        )

        _console.print(
            f"\n[bold cyan]Pipeline: {pipeline_def.name}[/bold cyan]\n")
        results = orch_runner.run(
            pipeline_def, args, pipeline_params=pipeline_params or None)

        for result in results:
            if result.status == "ok":
                _console.print(f"  [green]✓ {result.id:<20}[/green]  ok")
            elif result.status == "skipped":
                _console.print(
                    f"  [yellow]⊘ {result.id:<20}[/yellow]  skipped")
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

        if any(r.status == "failed" for r in results):
            sys.exit(1)
        return

    if args.describe:
        try:
            loader = ConfigLoader(config_path=data.path_config_file)
            ikctl_config = loader.load()
            repo = KitRepository(ikctl_config)
            kit_pipeline = repo.resolve(args.describe)
        except KitNotFoundError as exc:
            print(f"\nError: {exc}\n", file=sys.stderr)
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

    run_options = RunOptions(
        parameter=args.parameter,
        sudo=args.sudo,
        install=args.install,
        name=args.name,
        mode=args.mode,
        parallel_workers=getattr(args, "parallel_workers", None),
        dry_run=getattr(args, "dry_run", False),
        debug=getattr(args, "debug", False),
        stdout_output=getattr(args, "stdout", False),
        stderr_output=getattr(args, "stderr", False),
        context=getattr(args, "context", None),
        list=getattr(args, "list", None),
        strict=getattr(args, "strict", False),
        sudo_password=sudo_password,
        force_upload=getattr(args, "force_upload", False),
        remote_dir=getattr(args, "remote_dir", None),
    )
    runner = _build_runner(run_options, servers, secrets,
                           timeout_connect, timeout_exec, config_mode)
    try:
        Pipeline(
            runner=runner,
            options=run_options,
            servers=servers if args.host else None,
            sudo_password=sudo_password if args.host else None,
        )
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario.\n", file=sys.stderr)
        sys.exit(130)
    except RunnerError as exc:
        print(f"\nError: {exc}\n", file=sys.stderr)
        sys.exit(1)
