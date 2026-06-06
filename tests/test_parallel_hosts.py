"""Tests for parallel host execution in RemoteRunner."""
from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from ikctl.config.models import KitPipeline, ServerGroup
from ikctl.runner.remote import RemoteRunner
from ikctl.runner.result import RunResult


@pytest.fixture()
def kit():
    return KitPipeline(
        uploads=["/local/kits/mykit/script.sh"],
        pipeline=["bash .ikctl/mykit/script.sh"],
    )


@pytest.fixture()
def single_server():
    return ServerGroup(user="admin", port=22, hosts=["192.168.1.10"])


@pytest.fixture()
def two_servers():
    return ServerGroup(user="admin", port=22, hosts=["192.168.1.10", "10.0.0.5"])


@pytest.fixture()
def three_servers():
    return ServerGroup(user="admin", port=22, hosts=["host-a", "host-b", "host-c"])


def _make_connection(exec_result=("output line\n", "", 0)):
    """Build a mock IConnection that returns the given exec result."""
    conn = MagicMock()
    conn.exec_command.return_value = exec_result
    sftp_client = MagicMock()
    sftp_client.listdir.return_value = []
    conn.open_sftp.return_value = sftp_client
    return conn


# ---------------------------------------------------------------------------
# T9-a: Verify that N connections are created for N hosts
# ---------------------------------------------------------------------------

def test_creates_one_connection_per_host(kit, two_servers):
    created_for: list[str] = []

    def factory(host: str):
        created_for.append(host)
        return _make_connection()

    with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
        sftp_instance = MagicMock()
        sftp_instance.list_dir.return_value = []
        MockSftp.return_value = sftp_instance

        runner = RemoteRunner(connection_factory=factory)
        results = runner.run(kit, two_servers, object())

    assert sorted(created_for) == sorted(two_servers.hosts)
    assert len(results) == 2


def test_creates_three_connections_for_three_hosts(kit, three_servers):
    created_for: list[str] = []

    def factory(host: str):
        created_for.append(host)
        return _make_connection()

    with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
        sftp_instance = MagicMock()
        sftp_instance.list_dir.return_value = []
        MockSftp.return_value = sftp_instance

        runner = RemoteRunner(connection_factory=factory)
        results = runner.run(kit, three_servers, object())

    assert sorted(created_for) == sorted(three_servers.hosts)
    assert len(results) == 3


# ---------------------------------------------------------------------------
# T9-b: Verify that connection.close() is called for each host
# ---------------------------------------------------------------------------

def test_close_called_for_every_host_on_success(kit, two_servers):
    close_calls: list[str] = []

    def factory(host: str):
        conn = _make_connection()
        conn.close.side_effect = lambda: close_calls.append(host)
        return conn

    with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
        sftp_instance = MagicMock()
        sftp_instance.list_dir.return_value = []
        MockSftp.return_value = sftp_instance

        runner = RemoteRunner(connection_factory=factory)
        runner.run(kit, two_servers, object())

    assert sorted(close_calls) == sorted(two_servers.hosts)


def test_close_called_even_when_host_raises(kit, two_servers):
    close_calls: list[str] = []

    def factory(host: str):
        conn = MagicMock()
        conn.close.side_effect = lambda: close_calls.append(host)
        conn.exec_command.side_effect = RuntimeError("SSH error")
        sftp_client = MagicMock()
        sftp_client.listdir.return_value = []
        conn.open_sftp.return_value = sftp_client
        return conn

    with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
        MockSftp.side_effect = RuntimeError("SFTP init error")

        runner = RemoteRunner(connection_factory=factory)
        results = runner.run(kit, two_servers, object())

    assert sorted(close_calls) == sorted(two_servers.hosts)
    for result in results:
        assert result.success is False


# ---------------------------------------------------------------------------
# T9-c: If one host raises an exception, the others still return success=True
# ---------------------------------------------------------------------------

def test_failing_host_does_not_abort_other_hosts(kit, three_servers):
    fail_host = "host-b"

    def factory(host: str):
        if host == fail_host:
            conn = MagicMock()
            conn.exec_command.side_effect = RuntimeError("connection refused")
            sftp_client = MagicMock()
            sftp_client.listdir.return_value = []
            conn.open_sftp.return_value = sftp_client
            return conn
        return _make_connection()

    with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
        def sftp_factory(conn):
            instance = MagicMock()
            instance.list_dir.return_value = []
            return instance
        MockSftp.side_effect = lambda conn: (
            (_ for _ in ()).throw(RuntimeError("SFTP error"))
            if getattr(conn.exec_command, "side_effect", None) is not None
            else sftp_factory(conn)
        )

        runner = RemoteRunner(connection_factory=factory)
        results = runner.run(kit, three_servers, object())

    assert len(results) == 3
    result_by_host = {r.host: r for r in results}
    assert result_by_host["host-a"].success is True
    assert result_by_host["host-b"].success is False
    assert result_by_host["host-c"].success is True


def test_failing_host_result_has_success_false_and_others_true(kit, two_servers):
    fail_host = "192.168.1.10"

    def factory(host: str):
        if host == fail_host:
            conn = MagicMock()
            conn.close.return_value = None
            conn.exec_command.side_effect = RuntimeError("timeout")
            conn.open_sftp.return_value = MagicMock()
            return conn
        return _make_connection()

    with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
        def conditional_sftp(conn):
            if getattr(conn.exec_command, "side_effect", None) is not None:
                raise RuntimeError("SFTP error on failing host")
            inst = MagicMock()
            inst.list_dir.return_value = []
            return inst

        MockSftp.side_effect = conditional_sftp

        runner = RemoteRunner(connection_factory=factory)
        results = runner.run(kit, two_servers, object())

    assert len(results) == 2
    result_by_host = {r.host: r for r in results}
    assert result_by_host[fail_host].success is False
    assert result_by_host["10.0.0.5"].success is True


# ---------------------------------------------------------------------------
# T9-d: Verify that stdout of each RunResult contains the host prefix [host]
# ---------------------------------------------------------------------------

def test_stdout_lines_are_prefixed_with_host(kit, single_server):
    conn = _make_connection(exec_result=("some output\n", "", 0))

    with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
        sftp_instance = MagicMock()
        sftp_instance.list_dir.return_value = []
        MockSftp.return_value = sftp_instance

        runner = RemoteRunner(connection_factory=lambda host: conn)
        results = runner.run(kit, single_server, object())

    host = "192.168.1.10"
    result = results[0]
    assert result.host == host
    for line in result.stdout.splitlines():
        assert line.startswith(f"[{host}]"), f"Line not prefixed: {line!r}"


def test_stdout_prefix_contains_host_ip(kit, two_servers):
    def factory(host: str):
        return _make_connection(exec_result=(f"output from {host}\n", "", 0))

    with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
        sftp_instance = MagicMock()
        sftp_instance.list_dir.return_value = []
        MockSftp.return_value = sftp_instance

        runner = RemoteRunner(connection_factory=factory)
        results = runner.run(kit, two_servers, object())

    for result in results:
        for line in result.stdout.splitlines():
            assert line.startswith(f"[{result.host}]"), (
                f"Line for host {result.host} not prefixed: {line!r}"
            )


# ---------------------------------------------------------------------------
# T9-e: Verify that --parallel-workers 2 limits the ThreadPoolExecutor to 2
# ---------------------------------------------------------------------------

def test_parallel_workers_limits_concurrent_threads(kit, three_servers):
    """RemoteRunner with max_workers=2 uses at most 2 concurrent threads."""
    max_concurrent = 0
    lock = threading.Lock()
    active_count = 0

    original_map = ThreadPoolExecutor.map

    def counting_factory(host: str):
        nonlocal active_count, max_concurrent
        conn = _make_connection()
        return conn

    with patch("ikctl.runner.remote.ThreadPoolExecutor") as MockPool:
        pool_instance = MagicMock()
        MockPool.return_value.__enter__ = MagicMock(return_value=pool_instance)
        MockPool.return_value.__exit__ = MagicMock(return_value=False)

        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            sftp_instance.list_dir.return_value = []
            MockSftp.return_value = sftp_instance

            pool_instance.map.return_value = [
                RunResult(host=h, success=True, stdout=f"[{h}] ok", stderr="")
                for h in three_servers.hosts
            ]

            runner = RemoteRunner(connection_factory=counting_factory, max_workers=2)
            runner.run(kit, three_servers, object())

    MockPool.assert_called_once_with(max_workers=2)


def test_remote_runner_default_max_workers_is_4():
    """RemoteRunner defaults to max_workers=4."""
    runner = RemoteRunner(connection_factory=lambda host: _make_connection())
    assert runner._max_workers == 4


def test_remote_runner_accepts_custom_max_workers():
    """RemoteRunner stores the provided max_workers."""
    runner = RemoteRunner(connection_factory=lambda host: _make_connection(), max_workers=2)
    assert runner._max_workers == 2


def test_build_runner_passes_parallel_workers_to_remote_runner():
    """_build_runner passes parallel_workers from options to RemoteRunner."""
    from ikctl.main import _build_runner
    from ikctl.runner.remote import RemoteRunner as RR

    servers = ServerGroup(user="admin", port=22, hosts=["10.0.0.1"])
    options = SimpleNamespace(dry_run=False, mode="remote", parallel_workers=2)

    runner = _build_runner(options, servers, secrets="", timeout_connect=30.0, timeout_exec=120.0)

    assert isinstance(runner, RR)
    assert runner._max_workers == 2


def test_build_runner_uses_default_4_when_parallel_workers_missing():
    """_build_runner defaults to 4 workers when attribute is absent."""
    from ikctl.main import _build_runner
    from ikctl.runner.remote import RemoteRunner as RR

    servers = ServerGroup(user="admin", port=22, hosts=["10.0.0.1"])
    options = SimpleNamespace(dry_run=False, mode="remote")

    runner = _build_runner(options, servers, secrets="", timeout_connect=30.0, timeout_exec=120.0)

    assert isinstance(runner, RR)
    assert runner._max_workers == 4
