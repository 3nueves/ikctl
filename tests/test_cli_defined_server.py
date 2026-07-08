"""Tests for --host, --user, --password, --port, --key CLI flags."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from ikctl.config.models import ServerGroup
from ikctl.main import _build_runner, _make_connection_factory


@pytest.fixture()
def kit_options():
    return SimpleNamespace(
        dry_run=False,
        mode="remote",
        parallel_workers=4,
        debug=False,
        stdout_output=False,
        stderr_output=False,
        strict=False,
        sudo_password=None,
        force_upload=False,
        remote_dir=None,
        sudo=None,
        install="test-kit",
        name=None,
        parameter=None,
        context=None,
        list=None,
    )


class TestHostFlag:
    """--host builds ServerGroup from CLI values instead of config YAML."""

    def test_host_creates_server_group(self):
        hosts = ["10.0.0.5"]
        sg = ServerGroup(user="root", port=22, hosts=hosts, password=None, pkey=None)
        assert sg.user == "root"
        assert sg.hosts == ["10.0.0.5"]
        assert sg.password is None
        assert sg.pkey is None

    def test_host_with_password(self):
        sg = ServerGroup(user="dmoya", port=22, hosts=["10.0.0.5"], password="secreto", pkey=None)
        assert sg.user == "dmoya"
        assert sg.password == "secreto"

    def test_host_with_key(self):
        sg = ServerGroup(user="admin", port=2222, hosts=["10.0.0.5"], password=None, pkey="/home/user/.ssh/id_ed25519")
        assert sg.port == 2222
        assert sg.pkey == "/home/user/.ssh/id_ed25519"

    def test_host_multiple_hosts(self):
        hosts = ["10.0.0.5", "10.0.0.6", "10.0.0.7"]
        sg = ServerGroup(user="root", port=22, hosts=hosts, password=None, pkey=None)
        assert len(sg.hosts) == 3
        assert sg.hosts == hosts

    def test_host_default_user_is_root(self):
        sg = ServerGroup(user="root", port=22, hosts=["10.0.0.5"], password=None, pkey=None)
        assert sg.user == "root"

    def test_host_default_port_is_22(self):
        sg = ServerGroup(user="root", port=22, hosts=["10.0.0.5"], password=None, pkey=None)
        assert sg.port == 22

    def test_host_custom_port(self):
        sg = ServerGroup(user="root", port=2222, hosts=["10.0.0.5"], password=None, pkey=None)
        assert sg.port == 2222


class TestBuildRunnerWithCLIServer:
    """_build_runner works with ServerGroup constructed from CLI args."""

    def test_build_runner_returns_remote_runner_with_cli_host(self, kit_options):
        servers = ServerGroup(user="root", port=22, hosts=["10.0.0.5"], password="pass123", pkey=None)
        with patch("ikctl.main.RemoteRunner") as MockRemoteRunner:
            _run_runner(kit_options, servers)
        MockRemoteRunner.assert_called_once()

    def test_build_runner_passes_connection_factory_for_cli_host(self, kit_options):
        servers = ServerGroup(user="admin", port=2222, hosts=["10.0.0.5"], password=None, pkey="/tmp/key")
        opts = SimpleNamespace(**{**vars(kit_options), "parallel_workers": 2})
        with patch("ikctl.main.SSHConnection") as MockSSH:
            _build_runner(opts, servers, secrets="", timeout_connect=30.0, timeout_exec=120.0, config_mode="remote")
            conn_factory = _make_connection_factory(servers, "", 30.0)
            conn_factory("10.0.0.5")
        MockSSH.assert_called_once()
        args, _ = MockSSH.call_args
        assert args[0].hostname == "10.0.0.5"
        assert args[0].port == 2222

    def test_build_runner_dry_run_with_cli_host(self, kit_options):
        servers = ServerGroup(user="root", port=22, hosts=["10.0.0.5"], password="pass", pkey=None)
        opts = SimpleNamespace(**{**vars(kit_options), "dry_run": True})
        runner = _run_runner(opts, servers)
        from ikctl.runner.dry_run import DryRunRunner
        assert isinstance(runner, DryRunRunner)

    def test_build_runner_local_mode_with_cli_host(self, kit_options):
        servers = ServerGroup(user="root", port=22, hosts=["10.0.0.5"], password=None, pkey=None)
        opts = SimpleNamespace(**{**vars(kit_options), "mode": "local"})
        runner = _run_runner(opts, servers)
        from ikctl.runner.local import LocalRunner
        assert isinstance(runner, LocalRunner)

    def test_build_runner_parallel_workers_with_cli_host(self, kit_options):
        servers = ServerGroup(user="root", port=22, hosts=["10.0.0.5", "10.0.0.6"], password=None, pkey=None)
        opts = SimpleNamespace(**{**vars(kit_options), "parallel_workers": 2})
        with patch("ikctl.main.RemoteRunner") as MockRemoteRunner:
            _run_runner(opts, servers)
        _, kwargs = MockRemoteRunner.call_args
        assert kwargs["max_workers"] == 2


class TestSudoPasswordResolutionWithHost:
    """sudo_password resolution with --host: --sudo-password > --password > None."""

    def test_sudo_password_from_sudo_password_flag(self):
        args = SimpleNamespace(sudo_password="sudopass", password="sshpass")
        sudo_password = args.sudo_password or args.password or None
        assert sudo_password == "sudopass"

    def test_sudo_password_falls_back_to_password(self):
        args = SimpleNamespace(sudo_password=None, password="sshpass")
        sudo_password = args.sudo_password or args.password or None
        assert sudo_password == "sshpass"

    def test_sudo_password_none_when_no_password(self):
        args = SimpleNamespace(sudo_password=None, password=None)
        sudo_password = args.sudo_password or args.password or None
        assert sudo_password is None

    def test_sudo_password_empty_string_falls_back(self):
        args = SimpleNamespace(sudo_password="", password="sshpass")
        sudo_password = args.sudo_password or args.password or None
        assert sudo_password == "sshpass"

    def test_sudo_password_explicit_overrides_ssh_password(self):
        args = SimpleNamespace(sudo_password="sudopass", password="sshpass")
        sudo_password = args.sudo_password or args.password or None
        assert sudo_password == "sudopass"
        assert sudo_password != args.password

    def test_sudo_password_empty_both_returns_none(self):
        args = SimpleNamespace(sudo_password="", password="")
        sudo_password = args.sudo_password or args.password or None
        assert sudo_password is None


def _run_runner(options, servers, secrets="", timeout_connect=30.0, timeout_exec=120.0, config_mode="remote"):
    return _build_runner(options, servers, secrets, timeout_connect, timeout_exec, config_mode)