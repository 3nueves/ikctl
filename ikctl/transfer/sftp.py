"""SFTP file transfer using an IConnection."""
from __future__ import annotations

import hashlib
import logging

from ikctl.connection.interface import IConnection


class SftpTransfer:
    """Transfers files to a remote host via SFTP."""

    def __init__(self, connection: IConnection) -> None:
        """Open an SFTP session from the given connection."""
        self._connection = connection
        self._sftp = connection.open_sftp()
        self._logger = logging.getLogger(__name__)

    def upload(self, local_path: str, remote_path: str) -> None:
        """Upload a local file to a remote path."""
        self._logger.info("Uploading %s -> %s", local_path, remote_path)
        self._sftp.put(local_path, remote_path)

    def smart_upload(self, local_path: str, remote_path: str, force: bool = False) -> bool:
        """Upload only if changed. Returns True if uploaded, False if skipped."""
        if force:
            self._sftp.put(local_path, remote_path)
            return True

        local_hash = self._sha256(local_path)
        remote_hash = self._remote_sha256(remote_path)

        if remote_hash is not None and local_hash == remote_hash:
            self._logger.info("SKIP %s (unchanged)", remote_path)
            return False

        self._sftp.put(local_path, remote_path)
        return True

    @staticmethod
    def _sha256(path: str) -> str:
        """Return hex SHA256 of a local file."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def _remote_sha256(self, path: str) -> str | None:
        """Return hex SHA256 of a remote file, or None if it doesn't exist."""
        try:
            self._sftp.lstat(path)
        except FileNotFoundError:
            return None
        stdout, _, exit_code = self._connection.exec_command(f"sha256sum {path}")
        if exit_code != 0:
            return None
        return stdout.split()[0]

    def create_dir(self, path: str) -> None:
        """Create a directory on the remote host."""
        self._logger.info("Creating remote directory: %s", path)
        self._sftp.mkdir(path)

    def list_dir(self, path: str = ".") -> list[str]:
        """Return a list of file names in the remote directory."""
        return self._sftp.listdir(path)
