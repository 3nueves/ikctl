"""Tests for SSHConnection."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import paramiko
import pytest

from ikctl.exceptions import SSHConnectionError
from ikctl.connection.models import SSHOptions
from ikctl.connection.ssh import SSHConnection


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_transport_mock(pubkeys=("rsa-sha2-256", "rsa-sha2-512")):
    """Return a configured mock Transport."""
    transport = MagicMock()
    transport._preferred_pubkeys = pubkeys
    transport.get_remote_server_key.return_value = MagicMock()
    return transport


def _make_client_mock():
    """Return a configured mock SSHClient."""
    client = MagicMock()
    sftp = MagicMock()
    client.open_sftp.return_value = sftp
    return client


def _patch_transport(transport_mock):
    """Context-manager patch: paramiko.Transport returns transport_mock."""
    return patch("ikctl.connection.ssh.paramiko.Transport", return_value=transport_mock)


def _patch_socket():
    """Context-manager patch: socket.create_connection returns a MagicMock."""
    sock_mock = MagicMock()
    return patch("ikctl.connection.ssh.socket.create_connection", return_value=sock_mock), sock_mock


# ---------------------------------------------------------------------------
# Basic connection tests
# ---------------------------------------------------------------------------

@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_connect_with_key_filename(mock_client_cls):
    """SSHConnection authenticates with a key_filename via transport.auth_publickey."""
    transport = _make_transport_mock()
    mock_client = _make_client_mock()
    mock_client_cls.return_value = mock_client

    fake_pkey = MagicMock()

    with _patch_transport(transport), \
         patch("ikctl.connection.ssh.socket.create_connection"), \
         patch("ikctl.connection.ssh.paramiko.PKey.from_private_key_file", return_value=fake_pkey):

        opts = SSHOptions(
            hostname="host.example.com",
            username="deploy",
            key_filename="/home/deploy/.ssh/id_ed25519",
        )
        conn = SSHConnection(opts)

    transport.auth_publickey.assert_called_once_with("deploy", fake_pkey)
    conn.close()


@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_connect_with_password(mock_client_cls):
    """SSHConnection authenticates with password via transport.auth_password."""
    transport = _make_transport_mock()
    mock_client = _make_client_mock()
    mock_client_cls.return_value = mock_client

    with _patch_transport(transport), \
         patch("ikctl.connection.ssh.socket.create_connection"):

        opts = SSHOptions(
            hostname="host.example.com",
            username="deploy",
            password="s3cr3t",
            allow_agent=False,
            look_for_keys=False,
        )
        conn = SSHConnection(opts)

    transport.auth_password.assert_called_once_with("deploy", "s3cr3t")
    conn.close()


# ---------------------------------------------------------------------------
# close() and exec_command()
# ---------------------------------------------------------------------------

@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_close_closes_ssh_and_sftp(mock_client_cls):
    """close() closes the SFTP channel then the SSH client."""
    transport = _make_transport_mock()
    mock_client = _make_client_mock()
    mock_client_cls.return_value = mock_client

    with _patch_transport(transport), \
         patch("ikctl.connection.ssh.socket.create_connection"):

        opts = SSHOptions(hostname="host.example.com", username="deploy",
                          password="pw", allow_agent=False)
        conn = SSHConnection(opts)

    sftp = conn.open_sftp()
    conn.close()

    sftp.close.assert_called_once()
    mock_client.close.assert_called_once()


@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_exec_command_returns_stdout_stderr_exit_code(mock_client_cls):
    """exec_command() returns (stdout, stderr, exit_code) without printing."""
    transport = _make_transport_mock()
    mock_client = _make_client_mock()
    mock_client_cls.return_value = mock_client

    stdout_mock = MagicMock()
    stdout_mock.read.return_value = b"hello\n"
    stdout_mock.channel.recv_exit_status.return_value = 0

    stderr_mock = MagicMock()
    stderr_mock.read.return_value = b""

    mock_client.exec_command.return_value = (MagicMock(), stdout_mock, stderr_mock)

    with _patch_transport(transport), \
         patch("ikctl.connection.ssh.socket.create_connection"):

        opts = SSHOptions(hostname="host.example.com", username="deploy",
                          password="pw", allow_agent=False)
        conn = SSHConnection(opts)

    stdout, stderr, exit_code = conn.exec_command("echo hello")

    assert stdout == "hello\n"
    assert stderr == ""
    assert exit_code == 0

    conn.close()


# ---------------------------------------------------------------------------
# Keepalive
# ---------------------------------------------------------------------------

@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_keepalive_interval_calls_set_keepalive(mock_client_cls):
    """keepalive_interval > 0 calls transport.set_keepalive()."""
    transport = _make_transport_mock()
    mock_client = _make_client_mock()
    mock_client_cls.return_value = mock_client

    with _patch_transport(transport), \
         patch("ikctl.connection.ssh.socket.create_connection"):

        opts = SSHOptions(hostname="host.example.com", username="deploy",
                          keepalive_interval=60, password="pw", allow_agent=False)
        conn = SSHConnection(opts)

    transport.set_keepalive.assert_called_once_with(60)
    conn.close()


# ---------------------------------------------------------------------------
# ProxyCommand
# ---------------------------------------------------------------------------

@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_proxy_command_creates_proxy_command_socket(mock_client_cls):
    """proxy_command creates a ProxyCommand socket instead of a TCP connection."""
    transport = _make_transport_mock()
    mock_client = _make_client_mock()
    mock_client_cls.return_value = mock_client

    proxy_sock = MagicMock()

    with _patch_transport(transport), \
         patch("ikctl.connection.ssh.paramiko.ProxyCommand", return_value=proxy_sock) as mock_proxy, \
         patch("ikctl.connection.ssh.socket.create_connection") as mock_socket:

        opts = SSHOptions(
            hostname="host.example.com",
            username="deploy",
            proxy_command="ssh -W %h:%p jump.example.com",
            password="pw",
            allow_agent=False,
        )
        conn = SSHConnection(opts)

    mock_proxy.assert_called_once_with("ssh -W %h:%p jump.example.com")
    mock_socket.assert_not_called()
    conn.close()


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_oserror_raises_ssh_connection_error(mock_client_cls):
    """OSError from socket.create_connection causes SSHConnectionError."""
    mock_client_cls.return_value = _make_client_mock()

    opts = SSHOptions(hostname="host.example.com", username="deploy")
    with patch("ikctl.connection.ssh.socket.create_connection",
               side_effect=OSError("Network unreachable")):
        with pytest.raises(SSHConnectionError):
            SSHConnection(opts)


@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_authentication_exception_raises_ssh_connection_error(mock_client_cls):
    """transport.auth_password() raising AuthenticationException causes SSHConnectionError."""
    transport = _make_transport_mock()
    transport.auth_password.side_effect = paramiko.AuthenticationException("Auth failed")
    mock_client_cls.return_value = _make_client_mock()

    with _patch_transport(transport), \
         patch("ikctl.connection.ssh.socket.create_connection"):

        opts = SSHOptions(hostname="host.example.com", username="deploy",
                          password="bad", allow_agent=False)
        with pytest.raises(SSHConnectionError):
            SSHConnection(opts)


@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_ssh_negotiation_failure_raises_ssh_connection_error(mock_client_cls):
    """transport.start_client() raising SSHException causes SSHConnectionError."""
    transport = _make_transport_mock()
    transport.start_client.side_effect = paramiko.SSHException("Negotiation failed")
    mock_client_cls.return_value = _make_client_mock()

    with _patch_transport(transport), \
         patch("ikctl.connection.ssh.socket.create_connection"):

        opts = SSHOptions(hostname="host.example.com", username="deploy",
                          password="pw", allow_agent=False)
        with pytest.raises(SSHConnectionError):
            SSHConnection(opts)


@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_timeout_raises_ssh_connection_error(mock_client_cls):
    """TimeoutError from socket.create_connection causes SSHConnectionError."""
    mock_client_cls.return_value = _make_client_mock()

    opts = SSHOptions(hostname="host.example.com", username="deploy")
    with patch("ikctl.connection.ssh.socket.create_connection",
               side_effect=TimeoutError("Connection timed out")):
        with pytest.raises(SSHConnectionError):
            SSHConnection(opts)


@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_no_auth_method_raises_ssh_connection_error(mock_client_cls):
    """No auth method configured (no password, no key, no agent) raises SSHConnectionError."""
    transport = _make_transport_mock()
    mock_client_cls.return_value = _make_client_mock()

    with _patch_transport(transport), \
         patch("ikctl.connection.ssh.socket.create_connection"):

        opts = SSHOptions(
            hostname="host.example.com",
            username="deploy",
            password=None,
            key_filename=None,
            pkey=None,
            allow_agent=False,
        )
        with pytest.raises(SSHConnectionError):
            SSHConnection(opts)


# ---------------------------------------------------------------------------
# RSA legacy / SHA-1 compatibility
# ---------------------------------------------------------------------------

def test_paramiko_rsa_hashes_contains_sha1():
    """Installed Paramiko must include 'ssh-rsa' (SHA-1) in RSAKey.HASHES."""
    assert "ssh-rsa" in paramiko.RSAKey.HASHES


@patch("ikctl.connection.ssh.paramiko.SSHClient")
def test_rsa_legacy_server_ssh_rsa_only(mock_client_cls):
    """SSHConnection succeeds against a server that only advertises ssh-rsa (SHA-1)."""
    transport = _make_transport_mock(pubkeys=("ssh-rsa",))
    transport.server_extensions = {"server-sig-algs": b"ssh-rsa"}
    transport.auth_publickey.return_value = []
    mock_client_cls.return_value = _make_client_mock()

    fake_rsa_key = MagicMock(spec=paramiko.RSAKey)

    with _patch_transport(transport), \
         patch("ikctl.connection.ssh.socket.create_connection"), \
         patch.object(paramiko.RSAKey, "from_private_key_file", return_value=fake_rsa_key):

        opts = SSHOptions(
            hostname="legacy-host.example.com",
            username="deploy",
            key_filename="/home/deploy/.ssh/id_rsa",
        )
        conn = SSHConnection(opts)

    transport.auth_publickey.assert_called_once_with("deploy", fake_rsa_key)
    conn.close()
