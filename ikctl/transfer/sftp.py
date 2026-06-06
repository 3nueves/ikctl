"""SFTP file transfer using an IConnection."""
from __future__ import annotations

import logging

from ikctl.connection.base import IConnection


class SftpTransfer:
    """Transfers files to a remote host via SFTP."""

    def __init__(self, connection: IConnection) -> None:
        """Open an SFTP session from the given connection."""
        self._sftp = connection.open_sftp()
        self._logger = logging.getLogger(__name__)

    def upload(self, local_path: str, remote_path: str) -> None:
        """Upload a local file to a remote path."""
        self._logger.info("Uploading %s -> %s", local_path, remote_path)
        self._sftp.put(local_path, remote_path)

    def create_dir(self, path: str) -> None:
        """Create a directory on the remote host."""
        self._logger.info("Creating remote directory: %s", path)
        self._sftp.mkdir(path)

    def list_dir(self, path: str = ".") -> list[str]:
        """Return a list of file names in the remote directory."""
        return self._sftp.listdir(path)
