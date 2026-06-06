"""Tests for KitRepository auto-discovery."""
from __future__ import annotations

import pathlib

import pytest
import yaml

from ikctl.config.exceptions import KitNotFoundError
from ikctl.config.kit_repo import KitRepository
from ikctl.config.models import Context, IkctlConfig, KitPipeline


def _make_config(kits_path: str, exclude: list[str] | None = None) -> IkctlConfig:
    """Helper to build a minimal IkctlConfig pointing at the given kits path."""
    ctx = Context(
        name="local",
        path_kits=kits_path,
        path_servers=kits_path,
        path_secrets="",
        mode="local",
        exclude=exclude or [],
    )
    return IkctlConfig(context="local", contexts={"local": ctx})


def _write_kit_manifest(kit_dir: pathlib.Path) -> None:
    """Writes a minimal ikctl.yaml kit manifest into kit_dir."""
    kit_config = {
        "kits": {
            "uploads": ["file.sh"],
            "pipeline": ["install.sh"],
        }
    }
    with open(kit_dir / "ikctl.yaml", "w", encoding="utf-8") as f:
        yaml.dump(kit_config, f)


def test_resolve_discovers_kit_without_index(tmp_path: pathlib.Path) -> None:
    """resolve() finds a kit via rglob without requiring a root index file."""
    kit_dir = tmp_path / "docker"
    kit_dir.mkdir()
    _write_kit_manifest(kit_dir)

    config = _make_config(str(tmp_path))
    repo = KitRepository(config)
    result = repo.resolve("docker")

    assert isinstance(result, KitPipeline)
    assert len(result.uploads) == 1
    assert result.uploads[0].endswith("file.sh")
    assert len(result.pipeline) == 1
    assert result.pipeline[0].endswith("install.sh")


def test_resolve_nested_kit(tmp_path: pathlib.Path) -> None:
    """resolve() discovers kits in nested subdirectories and names them with their relative path."""
    nested_dir = tmp_path / "kubernetes" / "master"
    nested_dir.mkdir(parents=True)
    _write_kit_manifest(nested_dir)

    config = _make_config(str(tmp_path))
    repo = KitRepository(config)
    result = repo.resolve("kubernetes/master")

    assert isinstance(result, KitPipeline)
    assert len(result.uploads) == 1
    assert len(result.pipeline) == 1


def test_resolve_excludes_kit_from_list(tmp_path: pathlib.Path) -> None:
    """Kits listed in context.exclude are hidden from discovery."""
    kit_dir = tmp_path / "secret-kit"
    kit_dir.mkdir()
    _write_kit_manifest(kit_dir)

    config = _make_config(str(tmp_path), exclude=["secret-kit"])
    repo = KitRepository(config)

    with pytest.raises(KitNotFoundError):
        repo.resolve("secret-kit")


def test_resolve_ignores_root_ikctl_yaml(tmp_path: pathlib.Path) -> None:
    """The root ikctl.yaml index file is not treated as a kit."""
    root_index = {"kits": ["docker/ikctl.yaml"]}
    with open(tmp_path / "ikctl.yaml", "w", encoding="utf-8") as f:
        yaml.dump(root_index, f)

    kit_dir = tmp_path / "docker"
    kit_dir.mkdir()
    _write_kit_manifest(kit_dir)

    config = _make_config(str(tmp_path))
    repo = KitRepository(config)

    result = repo.resolve("docker")
    assert isinstance(result, KitPipeline)

    with pytest.raises(KitNotFoundError):
        repo.resolve("")


def test_resolve_raises_kit_not_found(tmp_path: pathlib.Path) -> None:
    """resolve() raises KitNotFoundError for a kit name that does not exist."""
    config = _make_config(str(tmp_path))
    repo = KitRepository(config)

    with pytest.raises(KitNotFoundError, match="nonexistent"):
        repo.resolve("nonexistent")


def test_list_kits_returns_all_discovered(tmp_path: pathlib.Path) -> None:
    """list_kits() returns names of all discovered kits."""
    for name in ("alpha", "beta"):
        d = tmp_path / name
        d.mkdir()
        _write_kit_manifest(d)

    config = _make_config(str(tmp_path))
    repo = KitRepository(config)
    kits = repo.list_kits()

    assert sorted(kits) == ["alpha", "beta"]


def test_list_kits_excludes_hidden(tmp_path: pathlib.Path) -> None:
    """list_kits() omits kits that are in the exclude list."""
    for name in ("visible", "hidden"):
        d = tmp_path / name
        d.mkdir()
        _write_kit_manifest(d)

    config = _make_config(str(tmp_path), exclude=["hidden"])
    repo = KitRepository(config)
    kits = repo.list_kits()

    assert "hidden" not in kits
    assert "visible" in kits


def test_list_kits_returns_empty_for_nonexistent_path(tmp_path: pathlib.Path) -> None:
    """list_kits() returns an empty list when path_kits does not exist."""
    config = _make_config(str(tmp_path / "does-not-exist"))
    repo = KitRepository(config)

    assert repo.list_kits() == []
