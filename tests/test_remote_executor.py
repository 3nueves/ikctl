"""Tests for RemoteExecutor."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ikctl.executor.remote import RemoteExecutor


@pytest.fixture()
def mock_connection():
    conn = MagicMock()
    return conn


def test_execute_returns_stdout_stderr_exit_code_on_success(mock_connection):
    mock_connection.exec_command.return_value = ("hello\n", "", 0)
    executor = RemoteExecutor(mock_connection)

    stdout, stderr, exit_code = executor.execute("echo hello")

    assert stdout == "hello\n"
    assert stderr == ""
    assert exit_code == 0
    mock_connection.exec_command.assert_called_once()
    args, kwargs = mock_connection.exec_command.call_args
    assert args[0] == "echo hello"
    assert kwargs.get("on_stdout") is None
    assert kwargs.get("on_stderr") is None


def test_execute_returns_nonzero_exit_code_on_failure(mock_connection):
    mock_connection.exec_command.return_value = ("", "command not found\n", 127)
    executor = RemoteExecutor(mock_connection)

    stdout, stderr, exit_code = executor.execute("bogus_cmd")

    assert stdout == ""
    assert stderr == "command not found\n"
    assert exit_code == 127


def test_execute_censors_password_in_log(mock_connection, caplog):
    mock_connection.exec_command.return_value = ("", "", 0)
    executor = RemoteExecutor(mock_connection)

    import logging
    with caplog.at_level(logging.INFO, logger="ikctl.executor.remote"):
        executor.execute("echo mysecret | sudo -S bash install.sh")

    assert "mysecret" not in caplog.text
    assert "***" in caplog.text


def test_execute_propagates_streaming_callbacks(mock_connection):
    """RemoteExecutor.execute() forwards on_stdout/on_stderr to the connection."""
    captured_stdout: list[str] = []
    captured_stderr: list[str] = []

    def on_stdout(line: str) -> None:
        captured_stdout.append(line)

    def on_stderr(line: str) -> None:
        captured_stderr.append(line)

    mock_connection.exec_command.return_value = ("out\n", "", 0)
    executor = RemoteExecutor(mock_connection)

    stdout, stderr, exit_code = executor.execute(
        "echo hello", on_stdout=on_stdout, on_stderr=on_stderr
    )

    assert stdout == "out\n"
    assert exit_code == 0
    args, kwargs = mock_connection.exec_command.call_args
    assert kwargs.get("on_stdout") is on_stdout
    assert kwargs.get("on_stderr") is on_stderr
