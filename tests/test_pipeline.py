"""Tests for Pipeline in pipeline.py."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ikctl.pipeline import Pipeline
from ikctl.exceptions import KitNotFoundError, ServerNotFoundError
from ikctl.runner.base import RunOptions, RunResult


def _options(**kwargs) -> RunOptions:
    """Return a RunOptions with sensible defaults."""
    defaults: dict = {"install": None, "list": None,
                "context": None, "name": "web", "dry_run": False}
    defaults.update(kwargs)
    return RunOptions(**defaults)


def _data_mock():
    """Return a Config mock with minimal working defaults."""
    m = MagicMock()
    m.load_config_file_kits.return_value = ({"kits": ["show-date"]}, "/kits")
    m.load_config_file_servers.return_value = (
        {"servers": [{"name": "web", "user": "u",
                      "port": 22, "password": "p", "hosts": ["h1"]}]},
        "/servers",
    )
    m.load_config_file_mode.return_value = "remote"
    m.extract_secrets.return_value = ("secret", "/secrets")
    m.extract_config_servers.return_value = {
        "user": "u", "port": 22, "hosts": ["h1"], "password": "p"}
    m.extract_config_kits.return_value = (["up.sh"], ["run.sh"])
    m.load_path_pipelines.return_value = None
    m.load_kit_pipelines.return_value = {}
    return m


def _ctx_mock() -> MagicMock:
    m = MagicMock()
    m.config = {"context": "dev", "contexts": ["dev"]}
    return m


def _make_pipeline(runner: MagicMock, options: RunOptions, data=None, ctx=None):
    """Construct a Pipeline with all external dependencies mocked."""

    with patch("ikctl.pipeline.Config", return_value=data or _data_mock()), \
            patch("ikctl.pipeline.Context", return_value=ctx or _ctx_mock()), \
            patch("ikctl.pipeline.Show"), \
            patch("ikctl.pipeline.Log"):
        return Pipeline(runner=runner, options=options)


@pytest.fixture()
def runner_mock() -> MagicMock:
    """Return a Runner mock with run() returning a successful RunResult by default."""
    m = MagicMock()
    m.run.return_value = [
        RunResult(host="h1", success=True, stdout="ok", stderr="")]
    return m


def test_run_calls_runner_run_when_install_is_set(runner_mock: MagicMock) -> None:
    """Pipeline must call runner.run exactly once when --install is provided."""
    _make_pipeline(runner_mock, _options(install="show-date"))
    runner_mock.run.assert_called_once()


def test_run_does_not_call_runner_run_when_install_is_not_set(runner_mock: MagicMock) -> None:
    """Pipeline must not call runner.run when --install is absent."""
    _make_pipeline(runner_mock, _options(list="kits"))
    runner_mock.run.assert_not_called()


def test_run_calls_show_config_when_list_is_set(runner_mock: MagicMock) -> None:
    """Pipeline must delegate --list to view.show_config with the right argument."""
    pipeline = _make_pipeline(runner_mock, _options(list="kits"))
    pipeline.view.show_config.assert_called_once_with("kits")


def test_run_calls_change_context_when_context_is_set(runner_mock: MagicMock) -> None:
    """Pipeline must call context.change_context when --context is provided."""
    ctx = _ctx_mock()
    _make_pipeline(runner_mock, _options(context="prod"), ctx=ctx)
    ctx.change_context.assert_called_once_with("prod")


def test_run_does_not_call_change_context_when_context_is_not_set(runner_mock: MagicMock) -> None:
    """Pipeline must not touch context when --context is absent."""
    ctx = _ctx_mock()
    _make_pipeline(runner_mock, _options(), ctx=ctx)
    ctx.change_context.assert_not_called()


def test_print_results_exits_when_any_result_fails(runner_mock: MagicMock) -> None:
    """Pipeline must call sys.exit(1) when at least one RunResult has success=False."""
    runner_mock.run.return_value = [
        RunResult(host="h1", success=False, stdout="", stderr="err")]
    with pytest.raises(SystemExit) as exc_info:
        _make_pipeline(runner_mock, _options(install="show-date"))
    assert exc_info.value.code == 1


def test_print_results_does_not_exit_when_all_succeed(runner_mock: MagicMock) -> None:
    """Pipeline must not call sys.exit when all RunResults are successful."""
    _make_pipeline(runner_mock, _options(install="show-date"))


def test_init_exits_when_server_not_found(runner_mock: MagicMock) -> None:
    """Pipeline must call sys.exit(1) when the requested server group does not exist."""
    data = _data_mock()
    data.extract_config_servers.side_effect = ServerNotFoundError(
        "web not found")
    with pytest.raises(SystemExit) as exc_info:
        _make_pipeline(runner_mock, _options(), data=data)
    assert exc_info.value.code == 1


def test_init_exits_when_kit_not_found(runner_mock: MagicMock) -> None:
    """Pipeline must call sys.exit(1) when the requested kit does not exist."""
    data = _data_mock()
    data.extract_config_kits.side_effect = KitNotFoundError(
        "missing-kit not found")
    with pytest.raises(SystemExit) as exc_info:
        _make_pipeline(runner_mock, _options(install="missing-kit"), data=data)
    assert exc_info.value.code == 1
