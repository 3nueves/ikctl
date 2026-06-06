"""Tests for ConfigLoader."""
from __future__ import annotations

import pathlib

import pytest
import yaml

from ikctl.config.exceptions import ConfigError
from ikctl.config.loader import ConfigLoader
from ikctl.config.models import IkctlConfig


@pytest.fixture()
def valid_config_file(tmp_path: pathlib.Path) -> pathlib.Path:
    """Creates a minimal valid ikctl config file."""
    config = {
        "context": "local",
        "contexts": {
            "local": {
                "path_kits": str(tmp_path / "kits"),
                "path_servers": str(tmp_path / "kits"),
                "path_secrets": "",
                "mode": "local",
            },
            "remote": {
                "path_kits": str(tmp_path / "kits"),
                "path_servers": str(tmp_path / "kits"),
                "path_secrets": "",
                "mode": "remote",
            },
        },
    }
    config_path = tmp_path / "config"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
    return config_path


def test_load_returns_ikctl_config(valid_config_file: pathlib.Path) -> None:
    """load() must return an IkctlConfig when the file is valid."""
    loader = ConfigLoader(config_path=valid_config_file)
    result = loader.load()
    assert isinstance(result, IkctlConfig)


def test_load_active_context(valid_config_file: pathlib.Path) -> None:
    """load() must expose the correct active context name."""
    loader = ConfigLoader(config_path=valid_config_file)
    result = loader.load()
    assert result.context == "local"


def test_load_contexts_keys(valid_config_file: pathlib.Path) -> None:
    """load() must expose all contexts as Context objects."""
    loader = ConfigLoader(config_path=valid_config_file)
    result = loader.load()
    assert "local" in result.contexts
    assert "remote" in result.contexts


def test_load_context_mode(valid_config_file: pathlib.Path) -> None:
    """Context objects must carry the correct mode."""
    loader = ConfigLoader(config_path=valid_config_file)
    result = loader.load()
    assert result.contexts["local"].mode == "local"
    assert result.contexts["remote"].mode == "remote"


def test_load_raises_config_error_when_file_missing(tmp_path: pathlib.Path) -> None:
    """load() must raise ConfigError when the config file does not exist."""
    loader = ConfigLoader(config_path=tmp_path / "nonexistent_config")
    with pytest.raises(ConfigError, match="not found"):
        loader.load()


def test_load_raises_config_error_when_file_malformed(tmp_path: pathlib.Path) -> None:
    """load() must raise ConfigError when the YAML is malformed (missing keys)."""
    config_path = tmp_path / "config"
    with open(config_path, "w", encoding="utf-8") as f:
        f.write("not_context: something\n")
    loader = ConfigLoader(config_path=config_path)
    with pytest.raises(ConfigError):
        loader.load()


def test_load_context_name_matches_key(valid_config_file: pathlib.Path) -> None:
    """Each Context object must have its name field equal to the dict key."""
    loader = ConfigLoader(config_path=valid_config_file)
    result = loader.load()
    for name, ctx in result.contexts.items():
        assert ctx.name == name
