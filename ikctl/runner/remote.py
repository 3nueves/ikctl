"""RemoteRunner: orchestrates kit execution on remote hosts."""
from __future__ import annotations

import logging
import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from rich.console import Console
from rich.markup import escape as _escape_markup
from rich.progress import Progress, SpinnerColumn, TextColumn

from ikctl.exceptions import KitNotFoundError, RunnerError, SSHConnectionError
from ikctl.config.models import KitPipeline, ServerGroup
from ikctl.connection.interface import IConnection
from ikctl.executor.remote import RemoteExecutor
from ikctl.runner.base import IRunner, RunOptions, RunResult
from ikctl.transfer.sftp import SftpTransfer

_console = Console(highlight=False)


def _build_remote_command(remote_dir: str, script: str, options: RunOptions, password: str) -> str:
    """Build the remote bash command using the remote directory where the script was uploaded."""
    params = " ".join(options.parameter) if options.parameter else ""
    sudo = options.sudo
    bash = "bash -eo pipefail" if options.strict else "bash"

    if sudo and params:
        return f"cd {remote_dir}; echo {password or ''} | sudo -S {bash} {script} {params}"
    if sudo:
        return f"cd {remote_dir}; echo {password or ''} | sudo -S {bash} {script}"
    if params:
        return f"cd {remote_dir}; {bash} {script} {params}"
    return f"cd {remote_dir}; {bash} {script}"


class RemoteRunner(IRunner):
    """Runs a kit on each host in a ServerGroup via SSH/SFTP."""

    def __init__(
        self,
        connection_factory: Callable[[str], IConnection],
        max_workers: int = 4,
    ) -> None:
        """Create a RemoteRunner using the given connection factory.

        The factory receives a hostname string and returns an IConnection.
        max_workers controls the maximum number of concurrent threads.
        """
        self._connection_factory = connection_factory
        self._max_workers = max_workers
        self._logger = logging.getLogger(__name__)

    def run(self, kit: KitPipeline, servers: ServerGroup, options: RunOptions) -> list[RunResult]:
        """Execute the kit on every host in servers concurrently. Returns one RunResult per host."""
        if not kit.uploads and not kit.pipeline:
            raise KitNotFoundError("Kit has no uploads and no pipeline steps.")

        progress = Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            console=_console,
            transient=False,
            disable=options.debug,
        )
        try:
            with progress:
                with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
                    results = list(pool.map(
                        lambda host: self._run_on_host(
                            host, kit, servers, options, progress),
                        servers.hosts,
                    ))
        except KeyboardInterrupt:
            self._logger.warning("Interrupted by user")
            raise

        return results

    def _run_on_host(
        self,
        host: str,
        kit: KitPipeline,
        servers: ServerGroup,
        options: RunOptions,
        progress: Progress,
    ) -> RunResult:
        """Execute the kit on a single host. Returns a RunResult with prefixed stdout lines."""
        self._logger.info("Starting on host: %s", host)
        conn = None
        label = f"[{_escape_markup(host)}]"
        task_id = progress.add_task(
            f"[dim][bold cyan]{label}[/bold cyan] connecting...[/dim]", total=None
        )
        try:
            conn = self._connection_factory(host)
            sftp = SftpTransfer(conn)
            executor = RemoteExecutor(conn)

            all_stdout: list[str] = []
            all_stderr: list[str] = []
            success = True

            # Upload all kit files
            for local_path in kit.uploads:
                remote_dir = f".ikctl/{kit.name}"
                remote_path = f"{remote_dir}/{os.path.basename(local_path)}"

                # Ensure remote directory exists
                existing = sftp.list_dir(
                    ".ikctl") if ".ikctl" in sftp.list_dir() else []
                if kit.name not in existing:
                    try:
                        sftp.create_dir(".ikctl")
                    except OSError:
                        pass
                    try:
                        sftp.create_dir(remote_dir)
                    except OSError:
                        pass

                fname = os.path.basename(local_path)
                progress.update(
                    task_id,
                    description=f"[dim][bold cyan]{label}[/bold cyan] UPLOAD  {_escape_markup(fname)}...[/dim]",
                )
                self._logger.info("UPLOAD: %s -> %s", local_path, remote_path)
                try:
                    uploaded = sftp.smart_upload(
                        local_path, remote_path, force=options.force_upload
                    )
                    action = "UPLOAD" if uploaded else "SKIP"
                    status = "[bold green]OK[/bold green]" if uploaded else "[bold yellow]unchanged[/bold yellow]"
                    progress.console.print(
                        f"[bold cyan]{label}[/bold cyan] {action:<7} {_escape_markup(fname):<40} {status}"
                    )
                except Exception:
                    if options.debug:
                        progress.console.print(
                            f"[bold cyan]{label}[/bold cyan] UPLOAD  {_escape_markup(fname):<40} [bold red]FAILED[/bold red]"
                        )
                    raise

            # Execute all pipeline steps
            password = options.sudo_password if options.sudo_password else (
                servers.password if hasattr(servers, "password") else None)
            for cmd in kit.pipeline:
                remote_dir = f".ikctl/{kit.name}"
                script = os.path.basename(cmd)
                full_cmd = _build_remote_command(
                    remote_dir, script, options, password)

                progress.update(
                    task_id,
                    description=f"[dim][bold cyan]{label}[/bold cyan] RUN     {_escape_markup(script)}...[/dim]",
                )
                stdout, stderr, exit_code = executor.execute(full_cmd)

                status_markup = "[bold green]OK[/bold green]" if exit_code == 0 else "[bold red]FAILED[/bold red]"
                progress.console.print(
                    f"[bold cyan]{label}[/bold cyan] RUN     {_escape_markup(script):<40} {status_markup}"
                )

                # Show stderr on failure only when --stderr flag is set
                if exit_code != 0 and options.stderr_output:
                    for line in stderr.splitlines():
                        progress.console.print(
                            f"[red]{_escape_markup(line)}[/red]")

                # Show stdout only with --stdout flag
                if options.stdout_output:
                    for line in stdout.splitlines():
                        progress.console.print(
                            f"[cyan]{label}[/cyan] {_escape_markup(line)}"
                        )

                all_stdout.extend(stdout.splitlines())
                all_stderr.extend(stderr.splitlines())

                if exit_code != 0:
                    success = False
                    self._logger.debug(
                        "Step failed (exit %d): %s", exit_code, stderr)
                    break

            return RunResult(
                host=host,
                success=success,
                stdout="\n".join(all_stdout),
                stderr="\n".join(all_stderr),
            )

        except (SSHConnectionError, OSError, RuntimeError) as exc:
            self._logger.error("Failed on host %s: %s", host, exc)
            progress.console.print(
                f"[bold cyan]{label}[/bold cyan] [bold red]FAILED[/bold red] {_escape_markup(str(exc))}"
            )
            return RunResult(host=host, success=False, stdout="", stderr=str(exc))
        except Exception as exc:  # noqa: BLE001
            self._logger.error("Unexpected error on host %s: %s", host, exc)
            raise RunnerError(
                f"Unexpected error on host {host}: {exc}") from exc
        finally:
            progress.remove_task(task_id)
            if conn is not None:
                conn.close()
