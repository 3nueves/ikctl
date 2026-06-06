"""Tests for SSHConnection."""
from __future__ import annotations

from unittest.mock import MagicMock, patch, call

import paramiko
import pytest

from ikctl.config.exceptions import SSHConnectionError
from ikctl.connection.options import SSHOptions
from ikctl.connection.ssh import SSHConnection


def _make_client_mock():
    """Return a configured mock SSHClient (no spec, class is already patched)."""
    client = MagicMock()
    sftp = MagicMock()
    client.open_sftp.return_value = sftp
    transport = MagicMock()
    client.get_transport.return_value = transport
    return client


@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_connect_with_key_filename(mock_client_cls):
    """SSHConnection calls client.connect with key_filename."""
    mock_client = _make_client_mock()
    mock_client_cls.return_value = mock_client

    opts = SSHOptions(
        hostname="host.example.com",
        username="deploy",
        key_filename="/home/deploy/.ssh/id_ed25519",
    )
    conn = SSHConnection(opts)

    call_kwargs = mock_client.connect.call_args.kwargs
    assert call_kwargs["hostname"] == "host.example.com"
    assert call_kwargs["key_filename"] == "/home/deploy/.ssh/id_ed25519"
    assert "password" not in call_kwargs

    conn.close()


@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_connect_with_password(mock_client_cls):
    """SSHConnection calls client.connect with password."""
    mock_client = _make_client_mock()
    mock_client_cls.return_value = mock_client

    opts = SSHOptions(
        hostname="host.example.com",
        username="deploy",
        password="s3cr3t",
        allow_agent=False,
        look_for_keys=False,
    )
    conn = SSHConnection(opts)

    call_kwargs = mock_client.connect.call_args.kwargs
    assert call_kwargs["password"] == "s3cr3t"
    assert call_kwargs["allow_agent"] is False
    assert call_kwargs["look_for_keys"] is False

    conn.close()


@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_close_closes_ssh_and_sftp(mock_client_cls):
    """close() closes the SFTP channel then the SSH client."""
    mock_client = _make_client_mock()
    mock_client_cls.return_value = mock_client

    opts = SSHOptions(hostname="host.example.com")
    conn = SSHConnection(opts)

    sftp = conn.open_sftp()
    conn.close()

    sftp.close.assert_called_once()
    mock_client.close.assert_called_once()


@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_exec_command_returns_stdout_stderr_exit_code(mock_client_cls):
    """exec_command() returns (stdout, stderr, exit_code) without printing."""
    mock_client = _make_client_mock()
    mock_client_cls.return_value = mock_client

    stdout_mock = MagicMock()
    stdout_mock.read.return_value = b"hello\n"
    stdout_mock.channel.recv_exit_status.return_value = 0

    stderr_mock = MagicMock()
    stderr_mock.read.return_value = b""

    mock_client.exec_command.return_value = (MagicMock(), stdout_mock, stderr_mock)

    opts = SSHOptions(hostname="host.example.com")
    conn = SSHConnection(opts)
    stdout, stderr, exit_code = conn.exec_command("echo hello")

    assert stdout == "hello\n"
    assert stderr == ""
    assert exit_code == 0

    conn.close()


@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_host_key_policy_reject_uses_reject_policy(mock_client_cls):
    """host_key_policy='reject' sets RejectPolicy on the client."""
    mock_client = _make_client_mock()
    mock_client_cls.return_value = mock_client

    opts = SSHOptions(hostname="host.example.com", host_key_policy="reject")
    conn = SSHConnection(opts)

    call_args = mock_client.set_missing_host_key_policy.call_args
    assert isinstance(call_args.args[0], paramiko.RejectPolicy)

    conn.close()


@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_keepalive_interval_calls_set_keepalive(mock_client_cls):
    """keepalive_interval > 0 calls transport.set_keepalive()."""
    mock_client = _make_client_mock()
    mock_client_cls.return_value = mock_client

    opts = SSHOptions(hostname="host.example.com", keepalive_interval=60)
    conn = SSHConnection(opts)

    transport = mock_client.get_transport.return_value
    transport.set_keepalive.assert_called_once_with(60)

    conn.close()


@patch("ikctl.connection.ssh.paramiko.ProxyCommand")
@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_proxy_command_passes_sock(mock_client_cls, mock_proxy_cmd):
    """proxy_command option sets sock=ProxyCommand(...) in client.connect."""
    mock_client = _make_client_mock()
    mock_client_cls.return_value = mock_client

    proxy_sock = MagicMock()
    mock_proxy_cmd.return_value = proxy_sock

    opts = SSHOptions(
        hostname="host.example.com",
        proxy_command="ssh -W %h:%p jump.example.com",
    )
    conn = SSHConnection(opts)

    mock_proxy_cmd.assert_called_once_with("ssh -W %h:%p jump.example.com")
    call_kwargs = mock_client.connect.call_args.kwargs
    assert call_kwargs["sock"] is proxy_sock

    conn.close()


@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_oserror_raises_ssh_connection_error(mock_client_cls):
    """client.connect() raising OSError causes SSHConnection.__init__ to raise SSHConnectionError."""
    mock_client = _make_client_mock()
    mock_client.connect.side_effect = OSError("Network unreachable")
    mock_client_cls.return_value = mock_client

    opts = SSHOptions(hostname="host.example.com", username="deploy")
    with pytest.raises(SSHConnectionError):
        SSHConnection(opts)


@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_authentication_exception_raises_ssh_connection_error(mock_client_cls):
    """client.connect() raising AuthenticationException causes SSHConnectionError."""
    mock_client = _make_client_mock()
    mock_client.connect.side_effect = paramiko.AuthenticationException("Auth failed")
    mock_client_cls.return_value = mock_client

    opts = SSHOptions(hostname="host.example.com", username="deploy")
    with pytest.raises(SSHConnectionError):
        SSHConnection(opts)


@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_bad_host_key_raises_ssh_connection_error(mock_client_cls):
    """client.connect() raising BadHostKeyException causes SSHConnectionError."""
    mock_client = _make_client_mock()
    mock_client.connect.side_effect = paramiko.BadHostKeyException(
        "host.example.com", MagicMock(), MagicMock()
    )
    mock_client_cls.return_value = mock_client

    opts = SSHOptions(hostname="host.example.com", username="deploy")
    with pytest.raises(SSHConnectionError):
        SSHConnection(opts)


@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_ssh_exception_raises_ssh_connection_error(mock_client_cls):
    """client.connect() raising SSHException causes SSHConnectionError."""
    mock_client = _make_client_mock()
    mock_client.connect.side_effect = paramiko.SSHException("Connection reset")
    mock_client_cls.return_value = mock_client

    opts = SSHOptions(hostname="host.example.com", username="deploy")
    with pytest.raises(SSHConnectionError):
        SSHConnection(opts)


@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_timeout_raises_ssh_connection_error(mock_client_cls):
    """client.connect() raising TimeoutError causes SSHConnectionError."""
    mock_client = _make_client_mock()
    mock_client.connect.side_effect = TimeoutError("Connection timed out")
    mock_client_cls.return_value = mock_client

    opts = SSHOptions(hostname="host.example.com", username="deploy")
    with pytest.raises(SSHConnectionError):
        SSHConnection(opts)
