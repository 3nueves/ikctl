"""Tests for SftpTransfer.smart_upload."""
from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ikctl.transfer.sftp import SftpTransfer


@pytest.fixture
def local_file():
    """Create a temporary file with known content and return its path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".sh") as f:
        f.write(b"echo hello\n")
        tmp_path = f.name
    yield tmp_path
    Path(tmp_path).unlink(missing_ok=True)


@pytest.fixture
def mock_connection():
    conn = MagicMock()
    conn.exec_command.return_value = ("dummy_hash  /path", "", 0)
    sftp_client = MagicMock()
    conn.open_sftp.return_value = sftp_client
    return conn


@pytest.fixture
def transfer(mock_connection):
    return SftpTransfer(mock_connection)


TEST_CONTENT = b"echo hello\n"
LOCAL_HASH = hashlib.sha256(TEST_CONTENT).hexdigest()


def test_upload_skips_when_unchanged(local_file, mock_connection):
    """When remote hash matches local, sftp.put should NOT be called."""
    mock_connection.exec_command.return_value = (
        f"{LOCAL_HASH}  /remote/script.sh", "", 0
    )
    sftp = SftpTransfer(mock_connection)

    result = sftp.smart_upload(local_file, "/remote/script.sh")

    assert result is False
    mock_connection.open_sftp.return_value.put.assert_not_called()


def test_upload_when_changed(local_file, mock_connection):
    """When remote hash differs, sftp.put should be called."""
    mock_connection.exec_command.return_value = (
        "different_hash  /remote/script.sh", "", 0
    )
    sftp = SftpTransfer(mock_connection)

    result = sftp.smart_upload(local_file, "/remote/script.sh")

    assert result is True
    mock_connection.open_sftp.return_value.put.assert_called_once()


def test_upload_when_remote_missing(local_file, mock_connection):
    """When remote file does not exist, sftp.put should be called."""
    sftp_client = mock_connection.open_sftp.return_value
    sftp_client.lstat.side_effect = FileNotFoundError
    sftp = SftpTransfer(mock_connection)

    result = sftp.smart_upload(local_file, "/remote/script.sh")

    assert result is True
    mock_connection.open_sftp.return_value.put.assert_called_once()


def test_force_upload_always_uploads(local_file, mock_connection):
    """With force=True, sftp.put should be called even if hashes match."""
    mock_connection.exec_command.return_value = (
        f"{LOCAL_HASH}  /remote/script.sh", "", 0
    )
    sftp = SftpTransfer(mock_connection)

    result = sftp.smart_upload(local_file, "/remote/script.sh", force=True)

    assert result is True
    mock_connection.open_sftp.return_value.put.assert_called_once()


def test_remote_exec_fallback_uploads(local_file, mock_connection):
    """When sha256sum on remote fails, sftp.put should be called (fallback)."""
    mock_connection.exec_command.return_value = (
        "", "sha256sum not found", 127
    )
    sftp = SftpTransfer(mock_connection)

    result = sftp.smart_upload(local_file, "/remote/script.sh")

    assert result is True
    mock_connection.open_sftp.return_value.put.assert_called_once()
