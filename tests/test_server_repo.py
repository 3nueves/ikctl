"""Tests for ServerRepository."""
from __future__ import annotations

import pathlib

import pytest
import yaml

from ikctl.exceptions import ServerNotFoundError
from ikctl.config.models import Context, IkctlConfig, ServerGroup
from ikctl.config.server_repo import ServerRepository


def _make_config(servers_path: str) -> IkctlConfig:
    """Helper to build a minimal IkctlConfig pointing at the given servers path."""
    ctx = Context(
        name="remote",
        path_kits=servers_path,
        path_servers=servers_path,
        path_secrets="",
        mode="remote",
    )
    return IkctlConfig(context="remote", contexts={"remote": ctx})


@pytest.fixture()
def servers_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """Creates a servers config with two groups."""
    servers = {
        "servers": [
            {
                "name": "alpha",
                "user": "admin",
                "hosts": ["10.0.0.1", "10.0.0.2"],
                "port": 22,
                "password": "secret",
            },
            {
                "name": "beta",
                "user": "deploy",
                "hosts": ["192.168.1.10"],
                "port": 2222,
                "password": "pass2",
            },
        ]
    }
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(servers, f)
    return tmp_path


def test_resolve_with_group_returns_server_group(servers_dir: pathlib.Path) -> None:
    """resolve('alpha') must return a ServerGroup for the named group."""
    config = _make_config(str(servers_dir))
    repo = ServerRepository(config)
    result = repo.resolve("alpha")
    assert isinstance(result, ServerGroup)


def test_resolve_with_group_correct_user(servers_dir: pathlib.Path) -> None:
    """resolve() must return the correct user for the named group."""
    config = _make_config(str(servers_dir))
    repo = ServerRepository(config)
    result = repo.resolve("alpha")
    assert result.user == "admin"


def test_resolve_with_group_correct_hosts(servers_dir: pathlib.Path) -> None:
    """resolve() must include all hosts for the named group."""
    config = _make_config(str(servers_dir))
    repo = ServerRepository(config)
    result = repo.resolve("alpha")
    assert result.hosts == ["10.0.0.1", "10.0.0.2"]


def test_resolve_none_returns_first_group(servers_dir: pathlib.Path) -> None:
    """resolve(None) must return the FIRST group, not the last."""
    config = _make_config(str(servers_dir))
    repo = ServerRepository(config)
    result = repo.resolve(None)
    assert result.user == "admin"
    assert result.hosts == ["10.0.0.1", "10.0.0.2"]


def test_resolve_second_group(servers_dir: pathlib.Path) -> None:
    """resolve('beta') must return the correct second group."""
    config = _make_config(str(servers_dir))
    repo = ServerRepository(config)
    result = repo.resolve("beta")
    assert result.user == "deploy"
    assert result.port == 2222


def test_resolve_raises_server_not_found_when_group_missing(servers_dir: pathlib.Path) -> None:
    """resolve() must raise ServerNotFoundError for an unknown group name."""
    config = _make_config(str(servers_dir))
    repo = ServerRepository(config)
    with pytest.raises(ServerNotFoundError, match="gamma"):
        repo.resolve("gamma")


def test_resolve_raises_server_not_found_when_config_missing(tmp_path: pathlib.Path) -> None:
    """resolve() must raise ServerNotFoundError when the servers config file is absent."""
    config = _make_config(str(tmp_path))
    repo = ServerRepository(config)
    with pytest.raises(ServerNotFoundError):
        repo.resolve(None)
