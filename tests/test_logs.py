"""Tests for the Log class in logs.py."""
from __future__ import annotations

import pytest

from ikctl.logs import Log


def test_stdout_success_no_message(capsys: pytest.CaptureFixture) -> None:
    """stdout() with check=0 and no logs prints 'End task successfully'."""
    Log().stdout(check=0)
    captured = capsys.readouterr()
    assert "End task successfully" in captured.out


def test_stdout_success_with_message(capsys: pytest.CaptureFixture) -> None:
    """stdout() with check=0 and a log message prints the message."""
    Log().stdout(logs="All done", check=0)
    captured = capsys.readouterr()
    assert "All done" in captured.out


def test_stdout_error_no_message(capsys: pytest.CaptureFixture) -> None:
    """stdout() with check!=0 and no errors prints 'End task with errors' to stderr."""
    Log().stdout(check=1)
    captured = capsys.readouterr()
    assert "End task with errors" in captured.err


def test_stdout_error_with_message(capsys: pytest.CaptureFixture) -> None:
    """stdout() with check!=0 and an error message prints the error to stderr."""
    Log().stdout(errors="Something failed", check=1)
    captured = capsys.readouterr()
    assert "Something failed" in captured.err


def test_stdout_typo_corrected(capsys: pytest.CaptureFixture) -> None:
    """stdout() must spell 'successfully' correctly, not 'succefully'."""
    Log().stdout(check=0)
    captured = capsys.readouterr()
    assert "succefully" not in captured.out
    assert "successfully" in captured.out
