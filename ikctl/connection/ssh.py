"""SSHConnection: paramiko-backed implementation of IConnection."""
from __future__ import annotations

import logging
import socket

import paramiko
from paramiko import agent as paramiko_agent

from ikctl.exceptions import SSHConnectionError
from ikctl.connection.interface import IConnection
from ikctl.connection.models import SSHOptions


class SSHConnection(IConnection):
    """Manages an SSH connection using paramiko."""

    def __init__(self, options: SSHOptions) -> None:
        """Open an SSH connection using the provided options."""
        self._options = options
        self._logger = logging.getLogger(__name__)
        self._sftp: paramiko.SFTPClient | None = None
        self._client = self._connect()

    def _connect(self) -> paramiko.SSHClient:
        """Create and return an authenticated SSHClient."""
        opts = self._options
        sock = self._create_socket()
        transport = self._create_transport(sock)
        self._verify_host_key(transport)
        self._authenticate(transport)
        if opts.keepalive_interval > 0:
            transport.set_keepalive(opts.keepalive_interval)
        client = paramiko.SSHClient()
        client._transport = transport  # type: ignore[attr-defined]
        return client

    def _create_socket(self) -> socket.socket | paramiko.ProxyCommand:
        """Return a raw socket or ProxyCommand for the connection."""
        opts = self._options
        try:
            if opts.proxy_command:
                return paramiko.ProxyCommand(opts.proxy_command)
            return socket.create_connection(
                (opts.hostname, opts.port), timeout=opts.timeout)
        except OSError as exc:
            raise SSHConnectionError(
                f"Network error connecting to {opts.hostname}: {exc}") from exc

    def _create_transport(
        self, sock: socket.socket | paramiko.ProxyCommand
    ) -> paramiko.Transport:
        """Create a paramiko Transport and complete SSH negotiation."""
        opts = self._options
        try:
            transport = paramiko.Transport(sock)
        except OSError as exc:
            raise SSHConnectionError(
                f"Network error connecting to {opts.hostname}: {exc}") from exc
        try:
            transport.start_client(timeout=opts.banner_timeout)
        except paramiko.SSHException as exc:
            transport.close()
            raise SSHConnectionError(
                f"SSH negotiation failed for {opts.hostname}: {exc}") from exc
        return transport

    def _build_policy(self) -> paramiko.MissingHostKeyPolicy:
        """Return the host key policy matching options.host_key_policy."""
        policies: dict[str, paramiko.MissingHostKeyPolicy] = {
            "auto_add": paramiko.AutoAddPolicy(),
            "reject": paramiko.RejectPolicy(),
            "warning": paramiko.WarningPolicy(),
        }
        policy = policies.get(self._options.host_key_policy)
        if policy is None:
            raise ValueError(
                f"Unknown host_key_policy: '{self._options.host_key_policy}'. "
                "Valid values: 'auto_add', 'reject', 'warning'."
            )
        return policy

    def _verify_host_key(self, transport: paramiko.Transport) -> None:
        """Verify the remote host key against the configured policy."""
        opts = self._options
        server_key = transport.get_remote_server_key()
        policy = self._build_policy()
        if isinstance(policy, paramiko.RejectPolicy):
            client_tmp = paramiko.SSHClient()
            client_tmp.load_system_host_keys()
            try:
                policy.missing_host_key(client_tmp, opts.hostname, server_key)
            except paramiko.SSHException as exc:
                transport.close()
                raise SSHConnectionError(
                    f"Host key rejected for {opts.hostname}: {exc}") from exc

    def _authenticate(self, transport: paramiko.Transport) -> None:
        """Authenticate the transport using the configured credentials."""
        opts = self._options
        if opts.username is None:
            transport.close()
            raise SSHConnectionError(f"No username configured for {opts.hostname}")
        username = opts.username
        try:
            if opts.key_filename is not None:
                self._auth_with_key_file(transport, username)
            elif opts.pkey is not None:
                self._auth_with_pkey(transport, username)
            elif opts.password is not None:
                self._auth_with_password(transport, username, opts.password)
            elif opts.allow_agent:
                self._auth_with_agent(transport, username)
            else:
                raise paramiko.AuthenticationException(
                    "No authentication method configured")
        except paramiko.AuthenticationException as exc:
            transport.close()
            raise SSHConnectionError(
                f"Authentication failed for {opts.hostname}: {exc}") from exc
        except paramiko.SSHException as exc:
            transport.close()
            raise SSHConnectionError(
                f"SSH error connecting to {opts.hostname}: {exc}") from exc

    def _auth_with_key_file(self, transport: paramiko.Transport, username: str) -> None:
        """Authenticate using a private key file, trying RSA, Ed25519 and ECDSA."""
        opts = self._options
        pkey = None
        for key_class in (paramiko.RSAKey, paramiko.Ed25519Key, paramiko.ECDSAKey):
            try:
                pkey = key_class.from_private_key_file(
                    opts.key_filename, password=opts.passphrase)  # type: ignore[arg-type]
                break
            except (paramiko.SSHException, ValueError):
                continue
        if pkey is None:
            raise paramiko.AuthenticationException(
                f"Could not load key: {opts.key_filename}")
        transport.auth_publickey(username, pkey)

    def _auth_with_pkey(self, transport: paramiko.Transport, username: str) -> None:
        """Authenticate using an in-memory PKey object."""
        opts = self._options
        if not isinstance(opts.pkey, paramiko.PKey):
            transport.close()
            raise SSHConnectionError(
                f"pkey must be a paramiko.PKey instance for {opts.hostname}")
        transport.auth_publickey(username, opts.pkey)

    def _auth_with_password(self, transport: paramiko.Transport, username: str, password: str) -> None:
        """Authenticate using a password."""
        transport.auth_password(username, password)

    def _auth_with_agent(self, transport: paramiko.Transport, username: str) -> None:
        """Authenticate using keys from the SSH agent."""
        agent = paramiko_agent.Agent()
        agent_keys = agent.get_keys()
        for key in agent_keys:
            try:
                transport.auth_publickey(username, key)
                return
            except paramiko.AuthenticationException:
                continue
        raise paramiko.AuthenticationException("No agent key worked")

    def exec_command(self, command: str) -> tuple[str, str, int]:
        """Execute a command remotely. Returns (stdout, stderr, exit_code)."""
        _, stdout_channel, stderr_channel = self._client.exec_command(command)
        exit_code = stdout_channel.channel.recv_exit_status()
        stdout = stdout_channel.read().decode("utf-8", errors="replace")
        stderr = stderr_channel.read().decode("utf-8", errors="replace")
        return stdout, stderr, exit_code

    def open_sftp(self) -> paramiko.SFTPClient:
        """Return an open SFTP client, reusing an existing one if available."""
        if self._sftp is None:
            self._sftp = self._client.open_sftp()
        return self._sftp

    def close(self) -> None:
        """Close the SFTP channel and SSH connection."""
        try:
            if self._sftp is not None:
                self._sftp.close()
        finally:
            self._client.close()
