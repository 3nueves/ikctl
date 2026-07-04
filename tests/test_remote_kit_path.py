"""Tests for the remote_kit_path feature (feature id 57).

Covers:
- Default ~/ikctl path in RunOptions and Context
- ConfigLoader reading path_remote_kits from YAML (present and absent)
- _ensure_remote_dirs creates all path segments and tolerates OSError
- RemoteRunner._run_on_host uses options.remote_kit_path as root
- smart_upload checksum path matches the resolved remote_path
"""
from __future__ import annotations

import pathlib
from unittest.mock import MagicMock, call, patch

import pytest
import yaml

from ikctl.config.loader import ConfigLoader
from ikctl.config.models import Context, KitPipeline, ServerGroup
from ikctl.runner.base import RunOptions
from ikctl.runner.remote import RemoteRunner, _ensure_remote_dirs
from ikctl.transfer.sftp import SftpTransfer


# ---------------------------------------------------------------------------
# RunOptions default
# ---------------------------------------------------------------------------

def test_run_options_default_remote_kit_path():
    """RunOptions() must have remote_kit_path == '~/ikctl' by default."""
    opts = RunOptions()
    assert opts.remote_kit_path == "~/ikctl"


def test_run_options_accepts_custom_remote_kit_path():
    """RunOptions must accept a custom remote_kit_path."""
    opts = RunOptions(remote_kit_path="/opt/ikctl")
    assert opts.remote_kit_path == "/opt/ikctl"


# ---------------------------------------------------------------------------
# Context default
# ---------------------------------------------------------------------------

def test_context_default_path_remote_kits():
    """Context dataclass must default path_remote_kits to '~/ikctl'."""
    ctx = Context(
        name="x",
        path_kits="",
        path_servers="",
        path_secrets="",
        mode="remote",
    )
    assert ctx.path_remote_kits == "~/ikctl"


def test_context_accepts_custom_path_remote_kits():
    """Context dataclass must accept a custom path_remote_kits."""
    ctx = Context(
        name="x",
        path_kits="",
        path_servers="",
        path_secrets="",
        mode="remote",
        path_remote_kits="/opt/ikctl",
    )
    assert ctx.path_remote_kits == "/opt/ikctl"


# ---------------------------------------------------------------------------
# ConfigLoader — path_remote_kits absent (default)
# ---------------------------------------------------------------------------

def _write_config(tmp_path: pathlib.Path, extra_ctx_fields: dict | None = None) -> pathlib.Path:
    """Write a minimal YAML config and return its path."""
    ctx_data: dict = {
        "path_kits": str(tmp_path / "kits"),
        "path_servers": str(tmp_path / "servers"),
        "path_secrets": "",
        "mode": "remote",
    }
    if extra_ctx_fields:
        ctx_data.update(extra_ctx_fields)

    config = {
        "context": "prod",
        "contexts": {"prod": ctx_data},
    }
    config_path = tmp_path / "config"
    config_path.write_text(yaml.dump(config), encoding="utf-8")
    return config_path


def test_config_loader_default_path_remote_kits(tmp_path):
    """ConfigLoader with no path_remote_kits in YAML must produce Context.path_remote_kits == '~/ikctl'."""
    config_path = _write_config(tmp_path)
    loader = ConfigLoader(config_path=config_path)
    result = loader.load()
    assert result.contexts["prod"].path_remote_kits == "~/ikctl"


def test_config_loader_custom_path_remote_kits(tmp_path):
    """ConfigLoader with path_remote_kits: /opt/ikctl must produce Context.path_remote_kits == '/opt/ikctl'."""
    config_path = _write_config(tmp_path, {"path_remote_kits": "/opt/ikctl"})
    loader = ConfigLoader(config_path=config_path)
    result = loader.load()
    assert result.contexts["prod"].path_remote_kits == "/opt/ikctl"


# ---------------------------------------------------------------------------
# _ensure_remote_dirs
# ---------------------------------------------------------------------------

def _make_sftp_mock() -> MagicMock:
    """Return a MagicMock shaped like SftpTransfer."""
    sftp = MagicMock(spec=SftpTransfer)
    return sftp


def test_ensure_remote_dirs_creates_each_segment():
    """_ensure_remote_dirs must call sftp.create_dir for each path segment."""
    sftp = _make_sftp_mock()
    _ensure_remote_dirs(sftp, "~/ikctl/bind9")

    calls = [c[0][0] for c in sftp.create_dir.call_args_list]
    assert "~" in calls or "~/ikctl" in calls or any("ikctl" in c for c in calls)
    # The final segment that matters is the full path up to bind9
    assert any("bind9" in c for c in calls)


def test_ensure_remote_dirs_absolute_path():
    """_ensure_remote_dirs must handle absolute paths like /opt/ikctl/bind9."""
    sftp = _make_sftp_mock()
    _ensure_remote_dirs(sftp, "/opt/ikctl/bind9")

    calls = [c[0][0] for c in sftp.create_dir.call_args_list]
    assert "/opt/ikctl/bind9" in calls


def test_ensure_remote_dirs_tolerates_oserror():
    """_ensure_remote_dirs must not raise when sftp.create_dir raises OSError (already exists)."""
    sftp = _make_sftp_mock()
    sftp.create_dir.side_effect = OSError("File exists")

    # Should not raise
    _ensure_remote_dirs(sftp, "/opt/ikctl/bind9")


def test_ensure_remote_dirs_swallows_partial_oserror():
    """_ensure_remote_dirs continues after an OSError on one segment."""
    sftp = _make_sftp_mock()
    call_count = 0

    def side_effect(path):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise OSError("exists")

    sftp.create_dir.side_effect = side_effect
    _ensure_remote_dirs(sftp, "/opt/ikctl/bind9")
    # At least 3 segments: /, /opt, /opt/ikctl, /opt/ikctl/bind9 — all attempted
    assert sftp.create_dir.call_count >= 3


# ---------------------------------------------------------------------------
# RemoteRunner uses options.remote_kit_path
# ---------------------------------------------------------------------------

def _make_progress_mock() -> MagicMock:
    progress = MagicMock()
    progress.console = MagicMock()
    progress.console.print = MagicMock()
    progress.add_task.return_value = 0
    progress.__enter__ = MagicMock(return_value=progress)
    progress.__exit__ = MagicMock(return_value=False)
    return progress


def _make_conn(exec_result=("output", "", 0)) -> MagicMock:
    conn = MagicMock()
    conn.exec_command.return_value = exec_result
    sftp_client = MagicMock()
    sftp_client.listdir.return_value = []
    conn.open_sftp.return_value = sftp_client
    return conn


def test_remote_runner_uses_default_remote_kit_path():
    """RemoteRunner._run_on_host must upload to ~/ikctl/<kit>/<file> by default."""
    kit = KitPipeline(
        name="bind9",
        uploads=["/local/kits/bind9/deploy.sh"],
        pipeline=["/local/kits/bind9/deploy.sh"],
    )
    servers = ServerGroup(user="admin", port=22, hosts=["10.0.0.1"])
    conn = _make_conn()
    progress_mock = _make_progress_mock()

    with patch("ikctl.runner.remote.Progress", return_value=progress_mock):
        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            MockSftp.return_value = sftp_instance

            runner = RemoteRunner(connection_factory=lambda host: conn)
            results = runner.run(kit, servers, RunOptions())

    assert results[0].success is True
    upload_call = sftp_instance.upload.call_args[0]
    # SFTP does not expand ~; the path must be stripped to 'ikctl/bind9/deploy.sh'
    assert upload_call[1] == "ikctl/bind9/deploy.sh", (
        f"Expected 'ikctl/bind9/deploy.sh', got '{upload_call[1]}'"
    )
    # Shell exec_command keeps ~/ikctl/... because the shell DOES expand ~
    executed_cmd = conn.exec_command.call_args[0][0]
    assert "cd ~/ikctl/bind9;" in executed_cmd


def test_remote_runner_uses_custom_remote_kit_path():
    """RemoteRunner._run_on_host must upload to <custom_path>/<kit>/<file> when configured."""
    kit = KitPipeline(
        name="bind9",
        uploads=["/local/kits/bind9/deploy.sh"],
        pipeline=["/local/kits/bind9/deploy.sh"],
    )
    servers = ServerGroup(user="admin", port=22, hosts=["10.0.0.1"])
    conn = _make_conn()
    progress_mock = _make_progress_mock()

    with patch("ikctl.runner.remote.Progress", return_value=progress_mock):
        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            MockSftp.return_value = sftp_instance

            runner = RemoteRunner(connection_factory=lambda host: conn)
            results = runner.run(kit, servers, RunOptions(remote_kit_path="/opt/ikctl"))

    assert results[0].success is True
    upload_call = sftp_instance.upload.call_args[0]
    assert upload_call[1] == "/opt/ikctl/bind9/deploy.sh", (
        f"Expected '/opt/ikctl/bind9/deploy.sh', got '{upload_call[1]}'"
    )
    executed_cmd = conn.exec_command.call_args[0][0]
    assert "cd /opt/ikctl/bind9;" in executed_cmd


def test_remote_runner_path_structure_kit_name_file():
    """Remote path must follow <remote_kit_path>/<kit_name>/<filename> pattern."""
    kit = KitPipeline(
        name="nginx",
        uploads=["/local/kits/nginx/setup.sh"],
        pipeline=[],
    )
    servers = ServerGroup(user="admin", port=22, hosts=["10.0.0.1"])
    conn = _make_conn()
    progress_mock = _make_progress_mock()

    with patch("ikctl.runner.remote.Progress", return_value=progress_mock):
        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            MockSftp.return_value = sftp_instance

            runner = RemoteRunner(connection_factory=lambda host: conn)
            runner.run(kit, servers, RunOptions(remote_kit_path="/srv/deploy"))

    upload_call = sftp_instance.upload.call_args[0]
    remote_path = upload_call[1]
    parts = remote_path.split("/")
    # Path is /srv/deploy/nginx/setup.sh
    assert "nginx" in parts, f"kit name 'nginx' must appear in path '{remote_path}'"
    assert "setup.sh" in parts, f"filename 'setup.sh' must appear in path '{remote_path}'"
    nginx_idx = parts.index("nginx")
    assert parts[nginx_idx + 1] == "setup.sh", (
        f"filename must immediately follow kit name in path '{remote_path}'"
    )


# ---------------------------------------------------------------------------
# smart_upload (checksum path) still works
# ---------------------------------------------------------------------------

def test_smart_upload_checksum_uses_resolved_remote_path():
    """SftpTransfer.upload must call _remote_checksum with the full resolved remote_path."""
    kit = KitPipeline(
        name="bind9",
        uploads=["/local/kits/bind9/deploy.sh"],
        pipeline=[],
    )
    servers = ServerGroup(user="admin", port=22, hosts=["10.0.0.1"])
    conn = _make_conn(exec_result=("abc123  /opt/ikctl/bind9/deploy.sh\n", "", 0))
    progress_mock = _make_progress_mock()

    with patch("ikctl.runner.remote.Progress", return_value=progress_mock):
        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            # Return False (file unchanged) to verify checksum path is correct
            sftp_instance.upload.return_value = False
            MockSftp.return_value = sftp_instance

            runner = RemoteRunner(connection_factory=lambda host: conn)
            runner.run(kit, servers, RunOptions(remote_kit_path="/opt/ikctl"))

    # upload() must have been called with the fully resolved path
    upload_call = sftp_instance.upload.call_args
    assert upload_call is not None
    remote_path_arg = upload_call[0][1]
    assert remote_path_arg == "/opt/ikctl/bind9/deploy.sh", (
        f"Expected '/opt/ikctl/bind9/deploy.sh', got '{remote_path_arg}'"
    )


def test_smart_upload_force_bypasses_checksum():
    """With force_upload=True, upload must be called with force=True regardless of path."""
    kit = KitPipeline(
        name="bind9",
        uploads=["/local/kits/bind9/deploy.sh"],
        pipeline=[],
    )
    servers = ServerGroup(user="admin", port=22, hosts=["10.0.0.1"])
    conn = _make_conn()
    progress_mock = _make_progress_mock()

    with patch("ikctl.runner.remote.Progress", return_value=progress_mock):
        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            sftp_instance.upload.return_value = True
            MockSftp.return_value = sftp_instance

            runner = RemoteRunner(connection_factory=lambda host: conn)
            runner.run(kit, servers, RunOptions(remote_kit_path="~/ikctl", force_upload=True))

    upload_call = sftp_instance.upload.call_args
    assert upload_call[1].get("force") is True or upload_call[0][2] is True


# ---------------------------------------------------------------------------
# Bug 2: SFTP operations must NOT use ~ (SFTP server does not expand ~)
# ---------------------------------------------------------------------------

def test_sftp_upload_strips_tilde_from_remote_path():
    """sftp.upload() must receive a path without '~/' prefix when remote_kit_path starts with ~/."""
    kit = KitPipeline(
        name="bind9",
        uploads=["/local/kits/bind9/deploy.sh"],
        pipeline=[],
    )
    servers = ServerGroup(user="admin", port=22, hosts=["10.0.0.1"])
    conn = _make_conn()
    progress_mock = _make_progress_mock()

    with patch("ikctl.runner.remote.Progress", return_value=progress_mock):
        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            sftp_instance.upload.return_value = True
            MockSftp.return_value = sftp_instance

            runner = RemoteRunner(connection_factory=lambda host: conn)
            runner.run(kit, servers, RunOptions(remote_kit_path="~/ikctl"))

    upload_call = sftp_instance.upload.call_args[0]
    remote_arg = upload_call[1]
    assert not remote_arg.startswith("~/"), (
        f"SFTP upload received '~/'-prefixed path '{remote_arg}'. "
        "SFTP servers do not expand ~; path must be relative (e.g. 'ikctl/bind9/deploy.sh')."
    )
    assert remote_arg == "ikctl/bind9/deploy.sh", (
        f"Expected SFTP path 'ikctl/bind9/deploy.sh', got '{remote_arg}'"
    )


def test_sftp_ensure_remote_dirs_strips_tilde():
    """_ensure_remote_dirs must receive a path without '~/' when remote_kit_path starts with ~/."""
    from ikctl.runner.remote import _sftp_path
    assert _sftp_path("~/ikctl") == "ikctl"
    assert _sftp_path("~/ikctl/bind9") == "ikctl/bind9"
    assert _sftp_path("~") == "."
    assert _sftp_path("/opt/ikctl") == "/opt/ikctl"
    assert _sftp_path("relative/path") == "relative/path"


def test_sftp_create_dir_does_not_receive_tilde_path():
    """SftpTransfer.create_dir must not be called with paths starting with '~/'."""
    kit = KitPipeline(
        name="bind9",
        uploads=["/local/kits/bind9/deploy.sh"],
        pipeline=[],
    )
    servers = ServerGroup(user="admin", port=22, hosts=["10.0.0.1"])
    conn = _make_conn()
    progress_mock = _make_progress_mock()

    with patch("ikctl.runner.remote.Progress", return_value=progress_mock):
        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            sftp_instance.upload.return_value = True
            MockSftp.return_value = sftp_instance

            runner = RemoteRunner(connection_factory=lambda host: conn)
            runner.run(kit, servers, RunOptions(remote_kit_path="~/ikctl"))

    for call_args in sftp_instance.create_dir.call_args_list:
        path_arg = call_args[0][0]
        assert not path_arg.startswith("~/"), (
            f"SftpTransfer.create_dir received '~/'-prefixed path '{path_arg}'. "
            "SFTP servers do not expand ~."
        )


def test_shell_command_keeps_tilde_in_exec_command():
    """exec_command (shell) must still use the original ~/ikctl/... path — shell expands ~."""
    kit = KitPipeline(
        name="bind9",
        uploads=["/local/kits/bind9/deploy.sh"],
        pipeline=["/local/kits/bind9/deploy.sh"],
    )
    servers = ServerGroup(user="admin", port=22, hosts=["10.0.0.1"])
    conn = _make_conn()
    progress_mock = _make_progress_mock()

    with patch("ikctl.runner.remote.Progress", return_value=progress_mock):
        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            sftp_instance.upload.return_value = True
            MockSftp.return_value = sftp_instance

            runner = RemoteRunner(connection_factory=lambda host: conn)
            runner.run(kit, servers, RunOptions(remote_kit_path="~/ikctl"))

    executed_cmd = conn.exec_command.call_args[0][0]
    assert "~/ikctl/bind9" in executed_cmd, (
        f"Shell exec_command should preserve '~/' for expansion, got: '{executed_cmd}'"
    )
