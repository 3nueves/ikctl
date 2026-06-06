"""Tests for DryRunRunner and --dry-run CLI flag integration."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from ikctl.config.models import KitPipeline, ServerGroup
from ikctl.runner.dry_run import DryRunRunner, _censor
from ikctl.runner.result import RunResult


@pytest.fixture()
def kit():
    return KitPipeline(
        uploads=["/home/user/kits/mykit/deploy.sh"],
        pipeline=["/home/user/kits/mykit/deploy.sh", "/home/user/kits/mykit/service.sh"],
    )


@pytest.fixture()
def servers():
    return ServerGroup(user="admin", port=22, hosts=["10.0.0.1", "10.0.0.2"])


@pytest.fixture()
def single_server():
    return ServerGroup(user="admin", port=22, hosts=["10.0.0.1"])


def test_dry_run_runner_returns_run_result_list(kit, servers):
    runner = DryRunRunner()
    results = runner.run(kit, servers, object())

    assert isinstance(results, list)
    assert len(results) == 2


def test_dry_run_runner_returns_success_true_for_each_host(kit, servers):
    runner = DryRunRunner()
    results = runner.run(kit, servers, object())

    for result in results:
        assert isinstance(result, RunResult)
        assert result.success is True


def test_dry_run_runner_prints_upload_paths(kit, single_server):
    runner = DryRunRunner()
    results = runner.run(kit, single_server, object())

    combined = "\n".join(r.stdout for r in results)
    assert "[DRY RUN] UPLOAD:" in combined
    assert "/home/user/kits/mykit/deploy.sh" in combined
    assert ".ikctl/mykit/deploy.sh" in combined
    assert "→" in combined


def test_dry_run_runner_prints_exec_for_each_pipeline_step(kit, single_server):
    runner = DryRunRunner()
    results = runner.run(kit, single_server, object())

    combined = "\n".join(r.stdout for r in results)
    assert "[DRY RUN] EXEC:" in combined
    assert "bash deploy.sh" in combined


def test_dry_run_runner_censors_passwords_in_commands(kit, single_server):
    options = SimpleNamespace(sudo="sudo", parameter=None)
    runner = DryRunRunner()
    results = runner.run(kit, single_server, options)

    combined = "\n".join(r.stdout for r in results)
    assert "echo *** |" in combined


def test_dry_run_runner_does_not_instantiate_ssh_connection(kit, single_server):
    with patch("ikctl.connection.ssh.SSHConnection") as MockSSH:
        runner = DryRunRunner()
        runner.run(kit, single_server, object())

        MockSSH.assert_not_called()


def test_dry_run_runner_does_not_instantiate_sftp_transfer(kit, single_server):
    with patch("ikctl.transfer.sftp.SftpTransfer") as MockSftp:
        runner = DryRunRunner()
        runner.run(kit, single_server, object())

        MockSftp.assert_not_called()


def test_dry_run_runner_prints_host_line_for_each_host(kit, servers):
    runner = DryRunRunner()
    results = runner.run(kit, servers, object())

    hosts_in_stdout = [r.stdout for r in results]
    assert any("10.0.0.1" in s for s in hosts_in_stdout)
    assert any("10.0.0.2" in s for s in hosts_in_stdout)


def test_censor_replaces_password_in_echo_pipe():
    cmd = "echo secretpass | sudo -S apt install -y nginx"
    result = _censor(cmd)
    assert "secretpass" not in result
    assert "echo *** |" in result


def test_censor_leaves_safe_commands_unchanged():
    cmd = "bash .ikctl/mykit/deploy.sh"
    assert _censor(cmd) == cmd


def test_build_runner_returns_dry_run_runner_when_flag_set():
    """_build_runner must return DryRunRunner when dry_run=True."""
    from ikctl.main import _build_runner
    from ikctl.runner.dry_run import DryRunRunner as DRR

    options = SimpleNamespace(dry_run=True, mode="remote")
    servers = ServerGroup(user="admin", port=22, hosts=["10.0.0.1"])

    runner = _build_runner(options, servers, secrets="", timeout_connect=30.0, timeout_exec=120.0)
    assert isinstance(runner, DRR)


def test_build_runner_returns_dry_run_runner_regardless_of_mode():
    """DryRunRunner is returned even when mode=local and dry_run=True."""
    from ikctl.main import _build_runner
    from ikctl.runner.dry_run import DryRunRunner as DRR

    options = SimpleNamespace(dry_run=True, mode="local")
    servers = ServerGroup(user="admin", port=22, hosts=["10.0.0.1"])

    runner = _build_runner(options, servers, secrets="", timeout_connect=30.0, timeout_exec=120.0)
    assert isinstance(runner, DRR)
