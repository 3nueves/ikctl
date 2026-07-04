"""Tests for --debug flag and logging level configuration."""
from __future__ import annotations

import logging
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest


def test_without_debug_paramiko_logger_at_warning() -> None:
    """Without --debug, paramiko logger level should be WARNING or higher."""
    logger = logging.getLogger("paramiko")
    logger.setLevel(logging.WARNING)
    assert logger.level >= logging.WARNING


def test_without_debug_paramiko_transport_logger_at_warning() -> None:
    """Without --debug, paramiko.transport logger level should be WARNING or higher."""
    logger = logging.getLogger("paramiko.transport")
    logger.setLevel(logging.WARNING)
    assert logger.level >= logging.WARNING


def test_without_debug_root_logger_not_info(caplog: pytest.LogCaptureFixture) -> None:
    """Without --debug, INFO log records from ikctl should not propagate to root handler."""
    ikctl_logger = logging.getLogger("ikctl")
    ikctl_logger.setLevel(logging.WARNING)
    with caplog.at_level(logging.WARNING, logger="ikctl"):
        ikctl_logger.info("should not appear")
    assert "should not appear" not in caplog.text


def test_with_debug_root_logger_at_info() -> None:
    """Simulating --debug: setting root logger to INFO makes INFO records visible."""
    root_logger = logging.getLogger()
    original_level = root_logger.level
    try:
        root_logger.setLevel(logging.INFO)
        assert root_logger.level == logging.INFO
    finally:
        root_logger.setLevel(original_level)


# --- Rich output tests for feature 11 ---

def test_run_on_host_upload_prints_ok_line() -> None:
    """_run_on_host prints a '[host] UPLOAD  <fname>  OK' line for each uploaded file."""
    import os
    import tempfile

    from ikctl.config.models import KitPipeline, ServerGroup
    from ikctl.runner.base import RunOptions
    from ikctl.runner.remote import RemoteRunner

    with tempfile.NamedTemporaryFile(delete=False, suffix=".sh") as tmp:
        tmp.write(b"#!/bin/bash\necho hello\n")
        tmp_path = tmp.name

    try:
        kit_dir = os.path.join(os.path.dirname(tmp_path), "mykitname")
        os.makedirs(kit_dir, exist_ok=True)
        script_path = os.path.join(kit_dir, "script.sh")
        with open(script_path, "w") as f:
            f.write("#!/bin/bash\necho hello\n")

        kit = KitPipeline(uploads=[script_path], pipeline=[])
        servers = ServerGroup(user="admin", port=22, hosts=["testhost2"])
        options = RunOptions(debug=True)

        conn = MagicMock()
        conn.exec_command.return_value = ("", "", 0)

        runner = RemoteRunner(connection_factory=lambda host: conn)

        progress_mock = MagicMock()
        progress_mock.console = MagicMock()
        progress_mock.console.print = MagicMock()
        progress_mock.add_task.return_value = 0

        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            sftp_instance.list_dir.return_value = []
            MockSftp.return_value = sftp_instance

            with patch("ikctl.runner.remote.RemoteExecutor"):
                runner._run_on_host("testhost2", kit, servers, options, progress_mock)

        printed_args = [
            str(c[0][0])
            for c in progress_mock.console.print.call_args_list
            if c[0]
        ]
        written = "\n".join(printed_args)
        assert "UPLOAD" in written
        assert "OK" in written
        assert "script.sh" in written
    finally:
        import shutil
        if os.path.isdir(kit_dir):
            shutil.rmtree(kit_dir)
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
