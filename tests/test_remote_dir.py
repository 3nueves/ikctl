"""Tests for remote_dir_configurable feature."""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from ikctl.config.models import KitPipeline, ServerGroup
from ikctl.runner.base import RunOptions
from ikctl.runner.utils import resolve_remote_dir


def test_default_remote_dir():
    """Default remote_dir is .ikctl/<kit.name>/ when neither CLI nor YAML set it."""
    kit = KitPipeline(uploads=[], pipeline=[], name="my-kit")
    options = RunOptions()
    result = resolve_remote_dir(kit, options)
    assert result == ".ikctl/my-kit"


def test_remote_dir_from_yaml():
    """KitPipeline.remote_dir from ikctl.yaml is used when CLI is not set."""
    kit = KitPipeline(uploads=[], pipeline=[], name="my-kit", remote_dir="/opt/my-app")
    options = RunOptions()
    result = resolve_remote_dir(kit, options)
    assert result == "/opt/my-app"


def test_remote_dir_from_cli():
    """CLI --remote-dir overrides kit.remote_dir."""
    kit = KitPipeline(uploads=[], pipeline=[], name="my-kit", remote_dir="/opt/my-app")
    options = RunOptions(remote_dir="/tmp/debug")
    result = resolve_remote_dir(kit, options)
    assert result == "/tmp/debug"


def test_remote_dir_cli_overrides_yaml():
    """When both CLI and YAML are set, CLI wins."""
    kit = KitPipeline(uploads=[], pipeline=[], name="my-kit", remote_dir="/opt/my-app")
    options = RunOptions(remote_dir="/tmp/debug")
    result = resolve_remote_dir(kit, options)
    assert result == "/tmp/debug"


def test_dry_run_uses_resolved_remote_dir():
    """DryRunRunner uses the resolved remote_dir in upload preview."""
    kit = KitPipeline(
        uploads=["/local/scripts/install.sh"],
        pipeline=["/local/scripts/run.sh"],
        name="my-kit",
        remote_dir="/opt/my-app",
    )
    servers = ServerGroup(user="ubuntu", port=22, hosts=["10.0.0.1"])
    options = RunOptions()

    from ikctl.runner.dry_run import DryRunRunner
    runner = DryRunRunner()
    results = runner.run(kit, servers, options)

    assert len(results) == 1
    assert "[DRY RUN] UPLOAD: /local/scripts/install.sh → /opt/my-app/install.sh" in results[0].stdout


def test_dry_run_cli_overrides_yaml():
    """DryRunRunner uses CLI remote_dir over YAML remote_dir."""
    kit = KitPipeline(
        uploads=["/local/scripts/install.sh"],
        pipeline=[],
        name="my-kit",
        remote_dir="/opt/my-app",
    )
    servers = ServerGroup(user="ubuntu", port=22, hosts=["10.0.0.1"])
    options = RunOptions(remote_dir="/tmp/debug")

    from ikctl.runner.dry_run import DryRunRunner
    runner = DryRunRunner()
    results = runner.run(kit, servers, options)

    assert len(results) == 1
    assert "[DRY RUN] UPLOAD: /local/scripts/install.sh → /tmp/debug/install.sh" in results[0].stdout


def test_remote_runner_uses_resolved_remote_dir():
    """RemoteRunner uses resolve_remote_dir for uploads and pipeline."""
    kit = KitPipeline(
        uploads=["/local/scripts/install.sh"],
        pipeline=["/local/scripts/run.sh"],
        name="my-kit",
        remote_dir="/opt/my-app",
    )
    servers = ServerGroup(user="ubuntu", port=22, hosts=["10.0.0.1"])
    options = RunOptions()

    conn = MagicMock()
    conn.open_sftp.return_value = MagicMock()
    conn.exec_command.return_value = ("output\n", "", 0)

    with patch("ikctl.runner.remote.SftpTransfer") as MockSftp, \
         patch("ikctl.runner.remote.RemoteExecutor") as MockExecutor:
        MockSftp.return_value.list_dir.return_value = []
        MockSftp.return_value.smart_upload.return_value = True
        MockExecutor.return_value.execute.return_value = ("output\n", "", 0)

        from ikctl.runner.remote import RemoteRunner
        runner = RemoteRunner(connection_factory=lambda host: conn)
        results = runner.run(kit, servers, options)

    assert len(results) == 1
    assert results[0].success is True

    # Verify smart_upload was called with the correct remote path
    MockSftp.return_value.smart_upload.assert_called_once()
    call_args = MockSftp.return_value.smart_upload.call_args
    assert call_args[0][1] == "/opt/my-app/install.sh"


def test_remote_runner_creates_parent_dir_for_custom_remote_dir():
    """When remote_dir is /opt/myapp, the runner creates /opt (parent) before /opt/myapp via ensure_dir."""
    kit = KitPipeline(
        uploads=["/local/scripts/install.sh"],
        pipeline=[],
        name="my-kit",
        remote_dir="/opt/myapp",
    )
    servers = ServerGroup(user="ubuntu", port=22, hosts=["10.0.0.1"])
    options = RunOptions()

    conn = MagicMock()
    conn.open_sftp.return_value = MagicMock()
    conn.exec_command.return_value = ("output\n", "", 0)

    with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
        MockSftp.return_value.list_dir.return_value = []

        from ikctl.runner.remote import RemoteRunner
        runner = RemoteRunner(connection_factory=lambda host: conn)
        runner.run(kit, servers, options)

    ensure_dir_calls = [c[0][0] for c in MockSftp.return_value.ensure_dir.call_args_list]
    assert "/opt/myapp" in ensure_dir_calls, (
        f"Expected ensure_dir('/opt/myapp') but got calls: {ensure_dir_calls}"
    )


def test_remote_runner_creates_ikctl_parent_for_default_remote_dir():
    """When remote_dir is .ikctl/mykit, the runner creates .ikctl/mykit via ensure_dir."""
    kit = KitPipeline(
        uploads=["/local/scripts/install.sh"],
        pipeline=[],
        name="mykit",
    )
    servers = ServerGroup(user="ubuntu", port=22, hosts=["10.0.0.1"])
    options = RunOptions()

    conn = MagicMock()
    conn.open_sftp.return_value = MagicMock()
    conn.exec_command.return_value = ("output\n", "", 0)

    with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
        MockSftp.return_value.list_dir.return_value = []

        from ikctl.runner.remote import RemoteRunner
        runner = RemoteRunner(connection_factory=lambda host: conn)
        runner.run(kit, servers, options)

    ensure_dir_calls = [c[0][0] for c in MockSftp.return_value.ensure_dir.call_args_list]
    assert ".ikctl/mykit" in ensure_dir_calls, (
        f"Expected ensure_dir('.ikctl/mykit') but got calls: {ensure_dir_calls}"
    )
