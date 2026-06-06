"""Tests for LocalExecutor."""
from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from ikctl.executor.local import LocalExecutor


def test_execute_returns_stdout_on_success():
    executor = LocalExecutor()
    stdout, stderr, exit_code = executor.execute("echo hello")

    assert "hello" in stdout
    assert exit_code == 0


def test_execute_returns_nonzero_exit_code_on_failure():
    executor = LocalExecutor()
    stdout, stderr, exit_code = executor.execute("exit 42")

    assert exit_code == 42


def test_execute_returns_timeout_error_when_timeout_expires():
    with patch("ikctl.executor.local.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="sleep 999", timeout=0.01)
        executor = LocalExecutor(timeout=0.01)
        stdout, stderr, exit_code = executor.execute("sleep 999")

    assert stdout == ""
    assert stderr == "Timeout expired"
    assert exit_code == 1
