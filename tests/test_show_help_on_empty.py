"""Tests for show_help_on_empty feature (id=22)."""
from __future__ import annotations

from io import StringIO
from unittest.mock import patch


def _invoke_main(*argv: str) -> tuple[int, str, str]:
    """Invoke ikctl.main.main() with the given argv and return (exit_code, stdout, stderr).

    Captures SystemExit, stdout and stderr. Never raises.
    """
    from ikctl.main import main

    fake_stdout = StringIO()
    fake_stderr = StringIO()

    exit_code = 0
    with patch("sys.argv", ["ikctl", *argv]):
        with patch("sys.stdout", fake_stdout):
            with patch("sys.stderr", fake_stderr):
                try:
                    main()
                except SystemExit as exc:
                    exit_code = int(exc.code) if exc.code is not None else 0

    return exit_code, fake_stdout.getvalue(), fake_stderr.getvalue()


def test_no_args_exits_zero() -> None:
    """ikctl without arguments must exit with code 0."""
    exit_code, stdout, stderr = _invoke_main()

    assert exit_code == 0, (
        f"Expected exit code 0 but got {exit_code}.\nstderr: {stderr}"
    )


def test_no_args_shows_help_text() -> None:
    """ikctl without arguments must print the help message."""
    exit_code, stdout, stderr = _invoke_main()

    # argparse writes help to stdout via print_help()
    combined = stdout + stderr
    assert "usage" in combined.lower(), (
        f"Expected help output containing 'usage' but got:\nstdout={stdout!r}\nstderr={stderr!r}"
    )
    assert "ikctl" in combined, (
        f"Expected help output containing 'ikctl' but got:\nstdout={stdout!r}\nstderr={stderr!r}"
    )


def test_help_flag_exits_zero() -> None:
    """ikctl --help must exit with code 0."""
    exit_code, stdout, stderr = _invoke_main("--help")

    assert exit_code == 0, (
        f"Expected exit code 0 but got {exit_code}.\nstderr: {stderr}"
    )


def test_help_flag_shows_help_text() -> None:
    """ikctl --help must print the help message."""
    exit_code, stdout, stderr = _invoke_main("--help")

    combined = stdout + stderr
    assert "usage" in combined.lower(), (
        f"Expected help output containing 'usage' but got:\nstdout={stdout!r}\nstderr={stderr!r}"
    )


def test_version_flag_exits_zero() -> None:
    """ikctl --version must exit with code 0."""
    exit_code, stdout, stderr = _invoke_main("--version")

    assert exit_code == 0, (
        f"Expected exit code 0 but got {exit_code}.\nstderr: {stderr}"
    )


def test_version_flag_shows_version_string() -> None:
    """ikctl --version must print a non-empty version string."""
    from ikctl.config.config import __version__

    exit_code, stdout, stderr = _invoke_main("--version")

    combined = stdout + stderr
    assert __version__ in combined, (
        f"Expected version '{__version__}' in output but got:\nstdout={stdout!r}\nstderr={stderr!r}"
    )
