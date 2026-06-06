"""Tests for LocalRunner."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ikctl.config.models import KitPipeline, ServerGroup
from ikctl.runner.local import LocalRunner
from ikctl.runner.result import RunResult


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

    results = runner.run(kit_two_steps, servers, object())

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

    results = runner.run(kit, servers, object())

    assert results[0].success is False
    assert executor.execute.call_count == 1


def test_run_with_empty_pipeline_returns_success(servers):
    executor = MagicMock()
    kit = KitPipeline(uploads=[], pipeline=[])
    runner = LocalRunner(executor)

    results = runner.run(kit, servers, object())

    assert results[0].host == "local"
    assert results[0].success is True
    executor.execute.assert_not_called()
