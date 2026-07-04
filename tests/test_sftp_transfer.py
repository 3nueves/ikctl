"""Tests for SftpTransfer."""
from __future__ import annotations

from unittest.mock import MagicMock

import paramiko

from ikctl.connection.interface import IConnection
from ikctl.transfer.sftp import SftpTransfer


def _make_connection_mock() -> IConnection:
    """Return a mock IConnection with a mock SFTPClient."""
    sftp = MagicMock(spec=paramiko.SFTPClient)
    connection = MagicMock(spec=IConnection)
    connection.open_sftp.return_value = sftp
    return connection


def test_upload_calls_sftp_put():
    """upload() calls sftp.put(local_path, remote_path)."""
    connection = _make_connection_mock()
    sftp = connection.open_sftp()
    transfer = SftpTransfer(connection)

    transfer.upload("/local/file.sh", "/remote/file.sh")

    sftp.put.assert_called_once_with("/local/file.sh", "/remote/file.sh")


def test_list_dir_returns_file_list():
    """list_dir() returns the list from sftp.listdir()."""
    connection = _make_connection_mock()
    sftp = connection.open_sftp()
    sftp.listdir.return_value = ["file1.sh", "file2.sh"]

    transfer = SftpTransfer(connection)
    result = transfer.list_dir("/remote/dir")

    sftp.listdir.assert_called_once_with("/remote/dir")
    assert result == ["file1.sh", "file2.sh"]


def test_create_dir_calls_sftp_mkdir():
    """create_dir() calls sftp.mkdir(path)."""
    connection = _make_connection_mock()
    sftp = connection.open_sftp()
    transfer = SftpTransfer(connection)

    transfer.create_dir("/remote/newdir")

    sftp.mkdir.assert_called_once_with("/remote/newdir")
