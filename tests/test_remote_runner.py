"""Tests for RemoteRunner."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ikctl.config.exceptions import KitNotFoundError, SSHConnectionError
from ikctl.config.models import KitPipeline, ServerGroup
from ikctl.runner.remote import RemoteRunner
from ikctl.runner.result import RunResult


@pytest.fixture()
def kit():
    return KitPipeline(uploads=["/local/kits/mykit/script.sh"], pipeline=["/local/kits/mykit/script.sh"])


@pytest.fixture()
def empty_kit():
    return KitPipeline(uploads=[], pipeline=[])


@pytest.fixture()
def servers():
    return ServerGroup(user="admin", port=22, hosts=["192.168.1.10"])


@pytest.fixture()
def multi_servers():
    return ServerGroup(user="admin", port=22, hosts=["host1", "host2"])


def _make_connection(exec_result=("output\n", "", 0)):
    conn = MagicMock()
    conn.exec_command.return_value = exec_result
    sftp_client = MagicMock()
    sftp_client.listdir.return_value = []
    conn.open_sftp.return_value = sftp_client
    return conn


def test_run_uploads_files_and_executes_pipeline(kit, servers):
    conn = _make_connection()
    runner = RemoteRunner(connection_factory=lambda host: conn)

    with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
        sftp_instance = MagicMock()
        sftp_instance.list_dir.return_value = []
        MockSftp.return_value = sftp_instance

        results = runner.run(kit, servers, object())

    assert len(results) == 1
    result = results[0]
    assert result.host == "192.168.1.10"
    assert result.success is True
    sftp_instance.upload.assert_called_once()
    conn.exec_command.assert_called_once_with("cd .ikctl/mykit; bash script.sh")


def test_run_raises_kit_not_found_for_empty_kit(empty_kit, servers):
    runner = RemoteRunner(connection_factory=lambda host: _make_connection())

    with pytest.raises(KitNotFoundError):
        runner.run(empty_kit, servers, object())


def test_run_calls_connection_close_even_when_execution_fails(kit, servers):
    conn = _make_connection(exec_result=("", "error", 1))

    with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
        sftp_instance = MagicMock()
        sftp_instance.list_dir.return_value = []
        MockSftp.return_value = sftp_instance

        runner = RemoteRunner(connection_factory=lambda host: conn)
        results = runner.run(kit, servers, object())

    conn.close.assert_called_once()
    assert results[0].success is False


def test_run_calls_connection_close_when_connection_factory_raises(kit, servers):
    closed = []

    class FailingConn:
        def exec_command(self, cmd):
            raise RuntimeError("SSH error")

        def open_sftp(self):
            raise RuntimeError("SFTP error")

        def close(self):
            closed.append(True)

    def bad_factory(host):
        conn = FailingConn()
        return conn

    with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
        MockSftp.side_effect = RuntimeError("SFTP error")
        runner = RemoteRunner(connection_factory=bad_factory)
        results = runner.run(kit, servers, object())

    assert results[0].success is False
    assert len(closed) == 1


def test_run_returns_result_per_host(kit, multi_servers):
    def factory(host):
        return _make_connection()

    with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
        sftp_instance = MagicMock()
        sftp_instance.list_dir.return_value = []
        MockSftp.return_value = sftp_instance

        runner = RemoteRunner(connection_factory=factory)
        results = runner.run(kit, multi_servers, object())

    assert len(results) == 2
    assert {r.host for r in results} == {"host1", "host2"}


def test_ssh_connection_error_returns_failed_run_result(kit, servers):
    """connection_factory raising SSHConnectionError returns RunResult(success=False) without propagating."""
    def failing_factory(host):
        raise SSHConnectionError("Auth failed")

    runner = RemoteRunner(connection_factory=failing_factory)
    results = runner.run(kit, servers, object())

    assert len(results) == 1
    result = results[0]
    assert result.success is False
    assert "Auth failed" in result.stderr
