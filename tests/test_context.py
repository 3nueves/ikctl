"""Tests for Context in context.py."""
from __future__ import annotations

import pathlib
from unittest.mock import MagicMock, patch

import pytest
import yaml

from ikctl.context import Context


def _write_config(path: pathlib.Path, contexts: list[str], active: str) -> pathlib.Path:
    """Write a minimal ikctl config YAML and return its path."""
    data = {"context": active, "contexts": {ctx: {} for ctx in contexts}}
    path.write_text(yaml.dump(data), encoding="utf-8")
    return path


def _make_context(config_file: pathlib.Path) -> Context:
    """Return a Context instance backed by the given config file."""
    mock_conf = MagicMock()
    mock_conf.path_config_file = str(config_file)
    with patch("ikctl.context.Config", return_value=mock_conf):
        return Context()


def test_check_context_exist_returns_true_for_existing_context(tmp_path: pathlib.Path) -> None:
    """check_context_exist must return True when the context key is present."""
    config_file = _write_config(tmp_path / "config", ["dev", "prod"], active="dev")
    ctx = _make_context(config_file)
    assert ctx.check_context_exist("prod") is True


def test_check_context_exist_returns_false_for_missing_context(tmp_path: pathlib.Path) -> None:
    """check_context_exist must return False when the context key is absent."""
    config_file = _write_config(tmp_path / "config", ["dev"], active="dev")
    ctx = _make_context(config_file)
    assert ctx.check_context_exist("staging") is False


def test_change_context_writes_new_active_context_to_file(tmp_path: pathlib.Path) -> None:
    """change_context must persist the new active context to the config file."""
    config_file = _write_config(tmp_path / "config", ["dev", "prod"], active="dev")
    ctx = _make_context(config_file)
    ctx.change_context("prod")
    saved = yaml.safe_load(config_file.read_text(encoding="utf-8"))
    assert saved["context"] == "prod"


def test_change_context_does_not_alter_other_contexts(tmp_path: pathlib.Path) -> None:
    """change_context must leave all context definitions intact."""
    config_file = _write_config(tmp_path / "config", ["dev", "prod"], active="dev")
    ctx = _make_context(config_file)
    ctx.change_context("prod")
    saved = yaml.safe_load(config_file.read_text(encoding="utf-8"))
    assert "dev" in saved["contexts"]
    assert "prod" in saved["contexts"]


def test_change_context_exits_when_context_does_not_exist(tmp_path: pathlib.Path) -> None:
    """change_context must call sys.exit(1) when the context is unknown."""
    config_file = _write_config(tmp_path / "config", ["dev"], active="dev")
    ctx = _make_context(config_file)
    with pytest.raises(SystemExit) as exc_info:
        ctx.change_context("nonexistent")
    assert exc_info.value.code == 1
