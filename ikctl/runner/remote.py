"""RemoteRunner: orchestrates kit execution on remote hosts."""
from __future__ import annotations

import logging
import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from rich.console import Console
from rich.live import Live
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
from rich.spinner import Spinner

from ikctl.config.exceptions import KitNotFoundError, SSHConnectionError
from ikctl.config.models import KitPipeline, ServerGroup
from ikctl.connection.base import IConnection
from ikctl.executor.remote import RemoteExecutor
from ikctl.runner.base import IRunner
from ikctl.runner.result import RunResult
from ikctl.transfer.sftp import SftpTransfer

_console = Console(stderr=False, highlight=False)


def _build_remote_command(remote_dir: str, script: str, options: object, password: str) -> str:
    """Build the remote bash command using the remote directory where the script was uploaded."""
    params = " ".join(options.parameter) if getattr(options, "parameter", None) else ""
    sudo = getattr(options, "sudo", None)

    if sudo and params:
        return f"cd {remote_dir}; echo {password} | sudo -S bash {script} {params}"
    elif sudo:
        return f"cd {remote_dir}; echo {password} | sudo -S bash {script}"
    elif params:
        return f"cd {remote_dir}; bash {script} {params}"
    else:
        return f"cd {remote_dir}; bash {script}"


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

    def run(self, kit: KitPipeline, servers: ServerGroup, options: object) -> list[RunResult]:
        """Execute the kit on every host in servers concurrently. Returns one RunResult per host."""
        if not kit.uploads and not kit.pipeline:
            raise KitNotFoundError("Kit has no uploads and no pipeline steps.")

        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            results = list(pool.map(
                lambda host: self._run_on_host(host, kit, servers, options),
                servers.hosts,
            ))

        return results

    def _run_on_host(self, host: str, kit: KitPipeline, servers: ServerGroup, options: object) -> RunResult:
        """Execute the kit on a single host. Returns a RunResult with prefixed stdout lines."""
        self._logger.info("Starting on host: %s", host)
        conn = None
        try:
            with Live(Spinner("dots", text=f"Connecting to {host}..."), console=_console, transient=False, refresh_per_second=10):
                conn = self._connection_factory(host)
            sftp = SftpTransfer(conn)
            executor = RemoteExecutor(conn)

            all_stdout: list[str] = []
            all_stderr: list[str] = []
            success = True

            # Upload all kit files
            with Progress(
                TextColumn("[cyan]{task.description}"),
                BarColumn(),
                TextColumn("{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                transient=True,
                console=_console,
            ) as progress:
                for local_path in kit.uploads:
                    kit_name = os.path.basename(os.path.dirname(local_path))
                    remote_dir = f".ikctl/{kit_name}"
                    remote_path = f"{remote_dir}/{os.path.basename(local_path)}"

                    # Ensure remote directory exists
                    existing = sftp.list_dir(".ikctl") if ".ikctl" in sftp.list_dir() else []
                    if kit_name not in existing:
                        try:
                            sftp.create_dir(".ikctl")
                        except OSError:
                            pass
                        try:
                            sftp.create_dir(remote_dir)
                        except OSError:
                            pass

                    try:
                        file_size = os.path.getsize(local_path)
                    except OSError:
                        file_size = 1
                    task = progress.add_task(
                        f"Uploading {os.path.basename(local_path)} to {host}",
                        total=file_size,
                    )
                    upload_line = f"UPLOAD: {local_path} -> {remote_path}"
                    self._logger.info(upload_line)
                    sftp.upload(local_path, remote_path)
                    progress.update(task, completed=file_size)
                    all_stdout.append(f"[{host}] {upload_line}")

            # Execute all pipeline steps
            password = servers.password if hasattr(servers, "password") else "no_pass"
            for cmd in kit.pipeline:
                kit_name = os.path.basename(os.path.dirname(cmd))
                remote_dir = f".ikctl/{kit_name}"
                script = os.path.basename(cmd)
                full_cmd = _build_remote_command(remote_dir, script, options, password)
                stdout, stderr, exit_code = executor.execute(full_cmd)
                for line in stdout.splitlines():
                    all_stdout.append(f"[{host}] {line}")
                all_stderr.extend(stderr.splitlines())
                if exit_code != 0:
                    success = False
                    self._logger.error("Step failed (exit %d): %s", exit_code, stderr)
                    break

            return RunResult(
                host=host,
                success=success,
                stdout="\n".join(all_stdout),
                stderr="\n".join(all_stderr),
            )

        except (SSHConnectionError, OSError, RuntimeError) as exc:
            self._logger.error("Failed on host %s: %s", host, exc)
            return RunResult(
                host=host,
                success=False,
                stdout="",
                stderr=str(exc),
            )
        finally:
            if conn is not None:
                conn.close()
