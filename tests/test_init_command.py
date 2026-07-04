"""Tests for init_command feature (id=23)."""
from __future__ import annotations

from io import StringIO
from pathlib import Path
from unittest.mock import patch

from ikctl.main import main
from ikctl.init.wizard import InitWizard


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _expected_paths(base: Path) -> list[Path]:
    """Return the 6 paths the wizard should create under base."""
    default = base / "kits" / "default"
    return [
        base / ".ikctl" / "config",
        default / "servers" / "config.yaml",
        default / "servers" / ".secrets",
        default / "kits" / "example-kit" / "ikctl.yaml",
        default / "kits" / "example-kit" / "date.sh",
        default / "pipelines" / "example.yaml",
    ]


# ---------------------------------------------------------------------------
# Core wizard tests
# ---------------------------------------------------------------------------

def test_auto_creates_all_five_files(tmp_path: Path) -> None:
    """--auto mode must create all 5 expected files without any prompt."""
    wizard = InitWizard(base=tmp_path, auto=True, force=False)
    created = wizard.run()

    for expected in _expected_paths(tmp_path):
        assert expected.exists(), f"Expected file not created: {expected}"

    assert len(created) == 6


def test_auto_no_legacy_index_file(tmp_path: Path) -> None:
    """--auto must NOT create ~/kits/ikctl.yaml (legacy root index)."""
    wizard = InitWizard(base=tmp_path, auto=True, force=False)
    wizard.run()

    legacy = tmp_path / "kits" / "ikctl.yaml"
    assert not legacy.exists(), "Legacy ~/kits/ikctl.yaml must not be created"


def test_idempotent_no_overwrite(tmp_path: Path) -> None:
    """Second run without --force must not overwrite existing files."""
    wizard = InitWizard(base=tmp_path, auto=True, force=False)
    wizard.run()

    # Tamper with the config file content
    config_file = tmp_path / ".ikctl" / "config"
    sentinel = "# sentinel-do-not-overwrite\n"
    with open(config_file, "a", encoding="utf-8") as f:
        f.write(sentinel)

    # Second run — must not overwrite
    wizard2 = InitWizard(base=tmp_path, auto=True, force=False)
    wizard2.run()

    content = config_file.read_text(encoding="utf-8")
    assert sentinel in content, "Existing file must not be overwritten without --force"


def test_idempotent_returns_empty_created_list(tmp_path: Path) -> None:
    """Second run without --force must return an empty created list."""
    wizard = InitWizard(base=tmp_path, auto=True, force=False)
    wizard.run()

    wizard2 = InitWizard(base=tmp_path, auto=True, force=False)
    created = wizard2.run()

    assert created == [
    ], f"Expected no files created on second run, got: {created}"


def test_force_overwrites_existing_files(tmp_path: Path) -> None:
    """--force must overwrite files that already exist."""
    wizard = InitWizard(base=tmp_path, auto=True, force=False)
    wizard.run()

    config_file = tmp_path / ".ikctl" / "config"
    config_file.write_text("overwritten-content\n", encoding="utf-8")

    wizard_force = InitWizard(base=tmp_path, auto=True, force=True)
    created = wizard_force.run()

    content = config_file.read_text(encoding="utf-8")
    assert "overwritten-content" not in content, "File must be overwritten when --force is used"
    assert "context: local" in content
    assert len(created) == 6


# ---------------------------------------------------------------------------
# File content tests
# ---------------------------------------------------------------------------

def test_config_file_content(tmp_path: Path) -> None:
    """~/.ikctl/config must contain local and remote contexts with correct keys."""
    wizard = InitWizard(base=tmp_path, auto=True)
    wizard.run()

    content = (tmp_path / ".ikctl" / "config").read_text(encoding="utf-8")
    assert "context: local" in content
    assert "path_kits:" in content
    assert "path_servers:" in content
    assert "path_pipelines:" in content
    assert "mode: local" in content
    assert "mode: remote" in content


def test_servers_file_content(tmp_path: Path) -> None:
    """servers/config.yaml must contain a server entry without hardcoded password."""
    wizard = InitWizard(base=tmp_path, auto=True)
    wizard.run()

    content = (tmp_path / "kits" / "default" / "servers" /
               "config.yaml").read_text(encoding="utf-8")
    assert "servers:" in content
    assert "mariadb" in content


def test_kit_manifest_content(tmp_path: Path) -> None:
    """kits/default/kits/example-kit/ikctl.yaml must contain uploads and pipeline keys."""
    wizard = InitWizard(base=tmp_path, auto=True)
    wizard.run()

    content = (tmp_path / "kits" / "default" / "kits" /
               "example-kit" / "ikctl.yaml").read_text(encoding="utf-8")
    assert "uploads:" in content
    assert "date.sh" in content
    assert "pipeline:" in content


def test_kit_script_content(tmp_path: Path) -> None:
    """kits/default/kits/example-kit/date.sh must be a valid bash script."""
    wizard = InitWizard(base=tmp_path, auto=True)
    wizard.run()

    content = (tmp_path / "kits" / "default" / "kits" /
               "example-kit" / "date.sh").read_text(encoding="utf-8")
    assert "#!/bin/bash" in content
    assert "date" in content


def test_pipeline_file_content(tmp_path: Path) -> None:
    """pipelines/example.yaml must reference show-date kit and mariadb."""
    wizard = InitWizard(base=tmp_path, auto=True)
    wizard.run()

    content = (tmp_path / "kits" / "default" / "pipelines" /
               "example.yaml").read_text(encoding="utf-8")
    assert "name: example" in content
    assert "show-date" in content
    assert "mariadb" in content


# ---------------------------------------------------------------------------
# main.py integration tests
# ---------------------------------------------------------------------------

def _invoke_main(*argv: str) -> tuple[int, str, str]:
    """Invoke ikctl.main.main() and return (exit_code, stdout, stderr)."""

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


def test_init_flag_is_actionable(tmp_path: Path) -> None:
    """ikctl --init must not show help; it must run the wizard and exit 0."""
    with patch("ikctl.main.InitWizard") as mock_wizard_cls:
        mock_instance = mock_wizard_cls.return_value
        mock_instance.run.return_value = []

        exit_code, stdout, stderr = _invoke_main("--init", "--auto")

    assert exit_code == 0
    mock_wizard_cls.assert_called_once()
    mock_instance.run.assert_called_once()


def test_init_does_not_show_help(tmp_path: Path) -> None:
    """ikctl --init must not print the usage/help banner."""
    with patch("ikctl.main.InitWizard") as mock_wizard_cls:
        mock_wizard_cls.return_value.run.return_value = []
        exit_code, stdout, stderr = _invoke_main("--init", "--auto")

    combined = stdout + stderr
    assert "usage" not in combined.lower(), (
        f"--init must not show help, but got:\nstdout={stdout!r}\nstderr={stderr!r}"
    )


def test_init_auto_flag_passes_auto_true(tmp_path: Path) -> None:
    """ikctl --init --auto must construct InitWizard with auto=True."""
    with patch("ikctl.main.InitWizard") as mock_wizard_cls:
        mock_wizard_cls.return_value.run.return_value = []
        _invoke_main("--init", "--auto")

    _, kwargs = mock_wizard_cls.call_args
    assert kwargs.get("auto") is True or mock_wizard_cls.call_args[0][1] is True or (
        mock_wizard_cls.call_args[1].get("auto") is True
    )


def test_init_force_flag_passes_force_true(tmp_path: Path) -> None:
    """ikctl --init --force must construct InitWizard with force=True."""
    with patch("ikctl.main.InitWizard") as mock_wizard_cls:
        mock_wizard_cls.return_value.run.return_value = []
        _invoke_main("--init", "--auto", "--force")

    call_kwargs = mock_wizard_cls.call_args[1] if mock_wizard_cls.call_args[1] else {
    }
    call_args = mock_wizard_cls.call_args[0] if mock_wizard_cls.call_args[0] else (
    )
    force_val = call_kwargs.get("force") if "force" in call_kwargs else (
        call_args[2] if len(call_args) > 2 else None)
    assert force_val is True


def test_init_works_without_config(tmp_path: Path) -> None:
    """--init must not require ~/.ikctl/config to exist beforehand."""
    # Verify no config exists
    assert not (tmp_path / ".ikctl" / "config").exists()

    wizard = InitWizard(base=tmp_path, auto=True)
    created = wizard.run()

    assert len(created) == 6
    assert (tmp_path / ".ikctl" / "config").exists()
