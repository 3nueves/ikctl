"""Tests for LocalRunner."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ikctl.config.models import KitPipeline, ServerGroup
from ikctl.runner.local import LocalRunner
from ikctl.runner.base import RunOptions


@pytest.fixture()
def servers():
    return ServerGroup(user="admin", port=22, hosts=["localhost"])


@pytest.fixture()
def kit_two_steps():
    return KitPipeline(uploads=[], pipeline=["step1.sh", "step2.sh"])


def test_run_executes_all_pipeline_steps(kit_two_steps, servers):
    executor = MagicMock()
    executor.execute.return_value = ("ok\n", "", 0)
    runner = LocalRunner(executor)

    results = runner.run(kit_two_steps, servers, RunOptions())

    assert len(results) == 1
    assert results[0].host == "local"
    assert results[0].success is True
    assert executor.execute.call_count == 2


def test_run_stops_on_first_failure(servers):
    executor = MagicMock()
    executor.execute.side_effect = [
        ("", "error\n", 1),
        ("ok\n", "", 0),
    ]
    kit = KitPipeline(uploads=[], pipeline=["fail.sh", "should_not_run.sh"])
    runner = LocalRunner(executor)

    results = runner.run(kit, servers, RunOptions())

    assert results[0].success is False
    assert executor.execute.call_count == 1


def test_run_with_empty_pipeline_returns_success(servers):
    executor = MagicMock()
    kit = KitPipeline(uploads=[], pipeline=[])
    runner = LocalRunner(executor)

    results = runner.run(kit, servers, RunOptions())

    assert results[0].host == "local"
    assert results[0].success is True
    executor.execute.assert_not_called()


def test_sudo_with_no_pass_uses_secrets_as_password():
    """When servers.password == 'no_pass', sudo command must use secrets content."""
    executor = MagicMock()
    executor.execute.return_value = ("ok\n", "", 0)
    runner = LocalRunner(executor, secrets="real_secret_pass")

    kit = KitPipeline(uploads=[], pipeline=["step1.sh"])
    servers = ServerGroup(user="admin", port=22, hosts=["localhost"], password="no_pass")
    runner.run(kit, servers, RunOptions(sudo="sudo"))

    executed_cmd = executor.execute.call_args[0][0]
    assert "real_secret_pass" in executed_cmd, (
        f"Expected 'real_secret_pass' in sudo command, got: '{executed_cmd}'"
    )
    assert "no_pass" not in executed_cmd, (
        f"'no_pass' must not appear in sudo command, got: '{executed_cmd}'"
    )


def test_sudo_with_real_password_uses_servers_password():
    """When servers.password is a real value (not 'no_pass'), sudo uses it directly."""
    executor = MagicMock()
    executor.execute.return_value = ("ok\n", "", 0)
    runner = LocalRunner(executor, secrets="should_not_be_used")

    kit = KitPipeline(uploads=[], pipeline=["step1.sh"])
    servers = ServerGroup(user="admin", port=22, hosts=["localhost"], password="mypassword")
    runner.run(kit, servers, RunOptions(sudo="sudo"))

    executed_cmd = executor.execute.call_args[0][0]
    assert "mypassword" in executed_cmd, (
        f"Expected 'mypassword' in sudo command, got: '{executed_cmd}'"
    )
    assert "should_not_be_used" not in executed_cmd, (
        f"secrets must not be used when servers.password is real, got: '{executed_cmd}'"
    )
