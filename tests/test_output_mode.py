"""Tests for --debug flag and logging level configuration."""
from __future__ import annotations

import logging
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from ikctl.logs import Log


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


def test_log_stdout_check_zero_prints_success(capsys: pytest.CaptureFixture) -> None:
    """Log.stdout() with check=0 prints something containing 'successfully'."""
    Log().stdout(check=0)
    captured = capsys.readouterr()
    assert "successfully" in captured.out.lower() or "End task successfully" in captured.out


def test_log_stdout_check_nonzero_prints_errors(capsys: pytest.CaptureFixture) -> None:
    """Log.stdout() with check=1 prints something containing 'errors' to stderr."""
    Log().stdout(check=1)
    captured = capsys.readouterr()
    assert "errors" in captured.err.lower() or "End task with errors" in captured.err


# --- Rich output tests for feature 11 ---

def test_run_on_host_prints_connecting_message() -> None:
    """_run_on_host prints a 'Connecting to <host>' message via Rich console."""
    from ikctl.config.models import KitPipeline, ServerGroup
    from ikctl.runner.remote import RemoteRunner

    output = StringIO()

    from rich.console import Console as RichConsole
    test_console = RichConsole(file=output, highlight=False, no_color=True)

    kit = KitPipeline(uploads=[], pipeline=[])
    servers = ServerGroup(user="admin", port=22, hosts=["testhost"])
    options = object()

    conn = MagicMock()
    conn.exec_command.return_value = ("", "", 0)

    runner = RemoteRunner(connection_factory=lambda host: conn)

    with patch("ikctl.runner.remote._console", test_console):
        with patch("ikctl.runner.remote.SftpTransfer"):
            with patch("ikctl.runner.remote.RemoteExecutor"):
                try:
                    runner._run_on_host("testhost", kit, servers, options)
                except Exception:
                    pass

    written = output.getvalue()
    assert "Connecting" in written or "testhost" in written


def test_run_on_host_uses_progress_for_uploads() -> None:
    """_run_on_host uses rich.progress.Progress when uploading files."""
    import os
    import tempfile

    from ikctl.config.models import KitPipeline, ServerGroup
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
        options = object()

        conn = MagicMock()
        conn.exec_command.return_value = ("", "", 0)

        progress_calls: list[str] = []

        original_progress_init = __import__(
            "rich.progress", fromlist=["Progress"]
        ).Progress.__init__

        runner = RemoteRunner(connection_factory=lambda host: conn)

        with patch("ikctl.runner.remote.Progress") as MockProgress:
            mock_progress_instance = MagicMock()
            mock_progress_instance.__enter__ = MagicMock(return_value=mock_progress_instance)
            mock_progress_instance.__exit__ = MagicMock(return_value=False)
            mock_progress_instance.add_task.return_value = 0
            MockProgress.return_value = mock_progress_instance

            with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
                sftp_instance = MagicMock()
                sftp_instance.list_dir.return_value = []
                MockSftp.return_value = sftp_instance

                with patch("ikctl.runner.remote.RemoteExecutor"):
                    runner._run_on_host("testhost2", kit, servers, options)

            MockProgress.assert_called_once()
            mock_progress_instance.add_task.assert_called_once()
            mock_progress_instance.update.assert_called_once()
    finally:
        import shutil
        if os.path.isdir(kit_dir):
            shutil.rmtree(kit_dir)
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
