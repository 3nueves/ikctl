"""SSHConnection: paramiko-backed implementation of IConnection."""
from __future__ import annotations

import logging
import socket

import paramiko

from ikctl.config.exceptions import SSHConnectionError
from ikctl.connection.base import IConnection
from ikctl.connection.options import SSHOptions


class SSHConnection(IConnection):
    """Manages an SSH connection using paramiko."""

    def __init__(self, options: SSHOptions) -> None:
        """Open an SSH connection using the provided options."""
        self._options = options
        self._logger = logging.getLogger(__name__)
        self._sftp: paramiko.SFTPClient | None = None
        self._client = self._connect()

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

    def _connect(self) -> paramiko.SSHClient:
        """Create and return an authenticated SSHClient."""
        opts = self._options
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(self._build_policy())

        connect_kwargs: dict = {
            "hostname": opts.hostname,
            "port": opts.port,
            "username": opts.username,
            "timeout": opts.timeout,
            "auth_timeout": opts.auth_timeout,
            "banner_timeout": opts.banner_timeout,
            "allow_agent": opts.allow_agent,
            "look_for_keys": opts.look_for_keys,
            "compress": opts.compress,
        }

        if opts.password is not None:
            connect_kwargs["password"] = opts.password

        if opts.passphrase is not None:
            connect_kwargs["passphrase"] = opts.passphrase

        if opts.key_filename is not None:
            connect_kwargs["key_filename"] = opts.key_filename

        if opts.pkey is not None:
            connect_kwargs["pkey"] = opts.pkey

        if opts.disabled_algorithms is not None:
            connect_kwargs["disabled_algorithms"] = opts.disabled_algorithms

        if opts.channel_timeout is not None:
            connect_kwargs["channel_timeout"] = opts.channel_timeout

        if opts.proxy_command is not None:
            connect_kwargs["sock"] = paramiko.ProxyCommand(opts.proxy_command)

        try:
            client.connect(**connect_kwargs)
        except paramiko.AuthenticationException as exc:
            raise SSHConnectionError(f"Authentication failed for {opts.hostname}: {exc}") from exc
        except paramiko.BadHostKeyException as exc:
            raise SSHConnectionError(f"Bad host key for {opts.hostname}: {exc}") from exc
        except paramiko.SSHException as exc:
            raise SSHConnectionError(f"SSH error connecting to {opts.hostname}: {exc}") from exc
        except (OSError, socket.timeout, TimeoutError) as exc:
            raise SSHConnectionError(f"Network error connecting to {opts.hostname}: {exc}") from exc

        if opts.keepalive_interval > 0:
            transport = client.get_transport()
            if transport is not None:
                transport.set_keepalive(opts.keepalive_interval)

        return client

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
