"""Tests for ConfigError handling in main() — bugfix id=29."""
from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from ikctl.main import main
from ikctl.exceptions import ConfigError


def _make_config_mock(*, raise_on_servers: bool = False) -> MagicMock:
    """Return a Config mock that optionally raises ConfigError on load_config_file_servers."""
    mock = MagicMock()
    if raise_on_servers:
        mock.load_config_file_servers.side_effect = ConfigError(
            "servers config not found"
        )
    else:
        mock.load_config_file_servers.return_value = ({}, None)
    mock.extract_secrets.return_value = ("", None)
    mock.load_config_file_mode.return_value = "remote"
    mock.load_timeout_connect.return_value = 30.0
    mock.load_timeout_exec.return_value = 120.0
    return mock


def test_load_config_file_servers_config_error_exits_1(capsys: pytest.CaptureFixture) -> None:
    """When load_config_file_servers raises ConfigError, main() prints to stderr and exits 1."""
    config_mock = _make_config_mock(raise_on_servers=True)

    with patch("ikctl.main.Config", return_value=config_mock):
        with patch.object(sys, "argv", ["ikctl", "-l", "servers"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

    assert exc_info.value.code == 1


def test_load_config_file_servers_config_error_stderr_message(capsys: pytest.CaptureFixture) -> None:
    """When load_config_file_servers raises ConfigError, message appears in stderr."""
    config_mock = _make_config_mock(raise_on_servers=True)

    with patch("ikctl.main.Config", return_value=config_mock):
        with patch.object(sys, "argv", ["ikctl", "-l", "servers"]):
            with pytest.raises(SystemExit):
                main()

    captured = capsys.readouterr()
    assert "servers config not found" in captured.err


def test_load_config_file_servers_config_error_no_traceback(capsys: pytest.CaptureFixture) -> None:
    """When load_config_file_servers raises ConfigError, no traceback appears in output."""
    config_mock = _make_config_mock(raise_on_servers=True)

    with patch("ikctl.main.Config", return_value=config_mock):
        with patch.object(sys, "argv", ["ikctl", "-l", "servers"]):
            with pytest.raises(SystemExit):
                main()

    captured = capsys.readouterr()
    assert "Traceback" not in captured.out
    assert "Traceback" not in captured.err
