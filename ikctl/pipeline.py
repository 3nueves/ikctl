"""Pipeline: orchestrates kit installation on remote or local servers."""
from __future__ import annotations

import logging
import sys

from rich.console import Console

from ikctl.config.config import Config
from ikctl.exceptions import KitNotFoundError, ServerNotFoundError
from ikctl.config.models import KitPipeline, ServerGroup
from ikctl.context import Context
from ikctl.logs import Log
from ikctl.runner.base import IRunner, RunOptions, RunResult
from ikctl.view import Show

_console = Console()
_error_console = Console(stderr=True)


class Pipeline:
    """Orchestrates the process of installing kits on remote or local servers."""

    def __init__(self, runner: IRunner, options: RunOptions) -> None:
        """Initialise Pipeline with an already-constructed runner and parsed options."""
        self._logger = logging.getLogger(__name__)
        self._runner = runner
        self.options = options
        self.log = Log()
        self.data = Config()

        self.config_kits, self.path_kits = self.data.load_config_file_kits()
        self.config_servers, self.path_servers = self.data.load_config_file_servers()
        self.config_mode = self.data.load_config_file_mode()
        self.secrets, self.path_secrets = self.data.extract_secrets()

        self.context = Context()
        self.config_contexts = self.context.config

        self.view = Show(
            list(self.config_kits["kits"]),
            self.path_kits,
            list(self.config_servers["servers"]),
            self.path_servers,
            self.config_contexts,
            self.config_mode,
            self.path_secrets,
            path_pipelines=self.data.load_path_pipelines(),
            kit_pipelines=self.data.load_kit_pipelines(),
        )

        try:
            servers_dict = self.data.extract_config_servers(
                self.config_servers, self.options.name)
        except ServerNotFoundError as exc:
            print(f"\nError: {exc}\n", file=sys.stderr)
            sys.exit(1)

        self.servers = ServerGroup(
            user=servers_dict["user"],
            port=servers_dict["port"],
            hosts=servers_dict["hosts"],
            password=servers_dict["password"],
            pkey=servers_dict.get("pkey"),
        )

        sudo_password = self.options.sudo_password
        if not sudo_password:
            sudo_password = self.secrets or None
        if not sudo_password:
            sudo_password = servers_dict.get("password") or None
        self.options.sudo_password = sudo_password

        self._run()

    def _print_results(self, results: list[RunResult]) -> None:
        """Print a summary line and exit with error if any host failed."""
        ok_count = sum(1 for r in results if r.success)
        failed_count = sum(1 for r in results if not r.success)
        if failed_count == 0:
            _console.print(
                f"\n[bold green]{ok_count} hosts OK, {failed_count} hosts FAILED[/bold green]")
        else:
            _console.print(
                f"\n[bold red]{ok_count} hosts OK, {failed_count} hosts FAILED[/bold red]")

        if not all(r.success for r in results):
            sys.exit(1)

    def _run(self) -> None:
        """Execute the pipeline based on parsed options."""
        if self.options.context:
            self.context.change_context(self.options.context)

        if self.options.list:
            self.view.show_config(self.options.list)

        if self.options.install:
            try:
                uploads, pipeline_steps = self.data.extract_config_kits(
                    self.config_kits, self.options.install)
            except KitNotFoundError as exc:
                print(f"\nError: {exc}\n", file=sys.stderr)
                sys.exit(1)
            kit = KitPipeline(uploads=uploads, pipeline=pipeline_steps)
            results = self._runner.run(kit, self.servers, self.options)
            self._print_results(results)
