"""Tests for --strict flag: verifies bash -eo pipefail is used when strict=True."""
from __future__ import annotations

from ikctl.runner.base import RunOptions
from ikctl.runner.remote import _build_remote_command


def test_without_strict_uses_bash():
    opts = RunOptions(strict=False)
    cmd = _build_remote_command(".ikctl/myscript", "run.sh", opts, None)
    assert "bash -eo pipefail" not in cmd
    assert "bash run.sh" in cmd


def test_with_strict_uses_pipefail():
    opts = RunOptions(strict=True)
    cmd = _build_remote_command(".ikctl/myscript", "run.sh", opts, None)
    assert "bash -eo pipefail run.sh" in cmd


def test_strict_with_sudo():
    opts = RunOptions(strict=True, sudo=True)
    cmd = _build_remote_command(".ikctl/myscript", "run.sh", opts, "secret")
    assert "sudo -S bash -eo pipefail run.sh" in cmd


def test_without_strict_with_sudo():
    opts = RunOptions(strict=False, sudo=True)
    cmd = _build_remote_command(".ikctl/myscript", "run.sh", opts, "secret")
    assert "sudo -S bash run.sh" in cmd
    assert "pipefail" not in cmd


def test_strict_with_params():
    opts = RunOptions(strict=True, parameter=["arg1", "arg2"])
    cmd = _build_remote_command(".ikctl/myscript", "run.sh", opts, None)
    assert "bash -eo pipefail run.sh arg1 arg2" in cmd
