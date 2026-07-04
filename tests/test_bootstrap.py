"""Tests for ConfigBootstrap covering directory structure and config file generation."""
from __future__ import annotations

import pathlib
from unittest.mock import patch

import yaml

from ikctl.config.bootstrap import ConfigBootstrap


def test_config_paths_contain_kits_dir(tmp_path: pathlib.Path) -> None:
    """path_kits must resolve to the default/kits subdirectory."""
    bootstrap = ConfigBootstrap(home=tmp_path, interactive=False)
    bootstrap.setup()

    config_file = tmp_path / ".ikctl" / "config"
    with open(config_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    for ctx_data in data["contexts"].values():
        assert "default/kits" in ctx_data["path_kits"]
        assert not ctx_data["path_kits"].startswith("$")
        assert "default/servers" in ctx_data["path_servers"]
        assert not ctx_data["path_servers"].startswith("$")


def test_servers_default_has_no_password(tmp_path: pathlib.Path) -> None:
    """Default servers config must not contain a hardcoded password placeholder."""
    bootstrap = ConfigBootstrap(home=tmp_path, interactive=False)
    bootstrap.setup()

    servers_yaml = tmp_path / "kits" / "default" / "servers" / "config.yaml"
    with open(servers_yaml, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    servers = data["servers"]
    assert all(s.get("password") is None for s in servers)


def test_no_legacy_kits_index_created(tmp_path: pathlib.Path) -> None:
    """bootstrap.setup() must NOT create ~/kits/ikctl.yaml (the legacy index)."""
    bootstrap = ConfigBootstrap(home=tmp_path, interactive=False)
    bootstrap.setup()

    legacy_file = tmp_path / "kits" / "ikctl.yaml"
    assert not legacy_file.exists(), "Legacy ~/kits/ikctl.yaml must not be created"


def test_setup_creates_example_kit(tmp_path: pathlib.Path) -> None:
    """setup() must create ~/kits/default/kits/example-kit/ikctl.yaml."""
    bootstrap = ConfigBootstrap(home=tmp_path, interactive=False)
    bootstrap.setup()

    kit_file = tmp_path / "kits" / "default" / "kits" / "example-kit" / "ikctl.yaml"
    assert kit_file.is_file(), "example-kit/ikctl.yaml must be created"


def test_setup_creates_example_pipeline(tmp_path: pathlib.Path) -> None:
    """setup() must create ~/kits/default/pipelines/example.yaml."""
    bootstrap = ConfigBootstrap(home=tmp_path, interactive=False)
    bootstrap.setup()

    pipeline_file = tmp_path / "kits" / "default" / "pipelines" / "example.yaml"
    assert pipeline_file.is_file(), "pipelines/example.yaml must be created"


def test_setup_creates_secrets_file(tmp_path: pathlib.Path) -> None:
    """setup() must create ~/kits/default/servers/.secrets."""
    bootstrap = ConfigBootstrap(home=tmp_path, interactive=False)
    bootstrap.setup()

    secrets_file = tmp_path / "kits" / "default" / "servers" / ".secrets"
    assert secrets_file.is_file(), "servers/.secrets must be created"


def test_config_contains_all_commented_optional_fields(tmp_path: pathlib.Path) -> None:
    """Config file must contain all optional Context fields as commented-out options."""
    bootstrap = ConfigBootstrap(home=tmp_path, interactive=False)
    bootstrap.setup()

    config_text = (tmp_path / ".ikctl" / "config").read_text(encoding="utf-8")
    for field in ("# timeout_connect", "# timeout_exec", "# exclude", "# kits_repo", "# kits_ref", "# kits_token"):
        assert field in config_text, f"Missing commented field: {field}"


def test_setup_skips_when_config_already_exists(tmp_path: pathlib.Path) -> None:
    """If ~/.ikctl/config already exists, setup() must not prompt and must not touch anything."""
    ikctl_dir = tmp_path / ".ikctl"
    ikctl_dir.mkdir(parents=True)
    config_file = ikctl_dir / "config"
    config_file.write_text("existing", encoding="utf-8")

    bootstrap = ConfigBootstrap(home=tmp_path, interactive=True)
    with patch("builtins.input") as mock_input:
        bootstrap.setup()

    mock_input.assert_not_called()
    assert config_file.read_text(encoding="utf-8") == "existing"


def test_interactive_yes_creates_structure(tmp_path: pathlib.Path) -> None:
    """When user answers 'yes', setup() creates the full directory structure."""
    bootstrap = ConfigBootstrap(home=tmp_path, interactive=True)
    with patch("builtins.input", return_value="yes"):
        bootstrap.setup()

    assert (tmp_path / ".ikctl" / "config").is_file()
    assert (tmp_path / "kits" / "default" /
            "servers" / "config.yaml").is_file()
    assert (tmp_path / "kits" / "default" / "kits" /
            "example-kit" / "ikctl.yaml").is_file()
    assert (tmp_path / "kits" / "default" /
            "pipelines" / "example.yaml").is_file()
    assert (tmp_path / "kits" / "default" / "servers" / ".secrets").is_file()


def test_interactive_no_creates_nothing(tmp_path: pathlib.Path) -> None:
    """When user answers 'no', setup() creates nothing."""
    bootstrap = ConfigBootstrap(home=tmp_path, interactive=True)
    with patch("builtins.input", return_value="no"):
        bootstrap.setup()

    assert not (tmp_path / ".ikctl").exists()
    assert not (tmp_path / "kits").exists()


def test_interactive_asks_only_once(tmp_path: pathlib.Path) -> None:
    """setup() must call input() exactly once regardless of how many dirs are missing."""
    bootstrap = ConfigBootstrap(home=tmp_path, interactive=True)
    with patch("builtins.input", return_value="yes") as mock_input:
        bootstrap.setup()

    mock_input.assert_called_once()


def test_setup_is_idempotent(tmp_path: pathlib.Path) -> None:
    """Calling setup() twice must not raise and must not overwrite existing files.

    Note: --force behavior (overwriting existing files) is handled by InitWizard, not
    ConfigBootstrap. That acceptance criterion is covered by
    tests/test_init_command.py::test_force_overwrites_existing_files.
    """
    bootstrap = ConfigBootstrap(home=tmp_path, interactive=False)
    bootstrap.setup()

    config_file = tmp_path / ".ikctl" / "config"
    original_content = config_file.read_text(encoding="utf-8")

    bootstrap.setup()

    assert config_file.read_text(encoding="utf-8") == original_content
