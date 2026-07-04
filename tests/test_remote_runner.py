"""Tests for RemoteRunner."""
from __future__ import annotations

from unittest.mock import MagicMock, patch, call

import pytest

from ikctl.exceptions import KitNotFoundError, SSHConnectionError
from ikctl.config.models import KitPipeline, ServerGroup
from ikctl.runner.remote import RemoteRunner
from ikctl.runner.base import RunOptions


@pytest.fixture()
def kit():
    return KitPipeline(name="mykit", uploads=["/local/kits/mykit/script.sh"], pipeline=["/local/kits/mykit/script.sh"])


@pytest.fixture()
def empty_kit():
    return KitPipeline(uploads=[], pipeline=[])


@pytest.fixture()
def servers():
    return ServerGroup(user="admin", port=22, hosts=["192.168.1.10"])


@pytest.fixture()
def multi_servers():
    return ServerGroup(user="admin", port=22, hosts=["host1", "host2"])


def _make_connection(exec_result=("output\n", "", 0)):
    conn = MagicMock()
    conn.exec_command.return_value = exec_result
    sftp_client = MagicMock()
    sftp_client.listdir.return_value = []
    conn.open_sftp.return_value = sftp_client
    return conn


def _make_progress_mock():
    """Return a mock Progress instance whose console.print records calls."""
    progress = MagicMock()
    progress.console = MagicMock()
    progress.console.print = MagicMock()
    progress.add_task.return_value = 0
    progress.__enter__ = MagicMock(return_value=progress)
    progress.__exit__ = MagicMock(return_value=False)
    return progress


def _printed_text(progress_mock):
    """Collect all strings passed to progress.console.print as a single joined string."""
    parts = []
    for c in progress_mock.console.print.call_args_list:
        args = c[0]
        if args:
            parts.append(str(args[0]))
    return "\n".join(parts)


def _patch_progress(progress_mock):
    """Return a context manager that patches ikctl.runner.remote.Progress."""
    return patch("ikctl.runner.remote.Progress", return_value=progress_mock)


def test_run_uploads_files_and_executes_pipeline(kit, servers):
    conn = _make_connection()
    runner = RemoteRunner(connection_factory=lambda host: conn)
    progress_mock = _make_progress_mock()

    with _patch_progress(progress_mock):
        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            sftp_instance.list_dir.return_value = []
            MockSftp.return_value = sftp_instance

            results = runner.run(kit, servers, RunOptions())

    assert len(results) == 1
    result = results[0]
    assert result.host == "192.168.1.10"
    assert result.success is True
    sftp_instance.upload.assert_called_once()
    conn.exec_command.assert_called_once_with(
        "cd .ikctl/mykit; bash script.sh")


def test_run_raises_kit_not_found_for_empty_kit(empty_kit, servers):
    runner = RemoteRunner(connection_factory=lambda host: _make_connection())

    with pytest.raises(KitNotFoundError):
        runner.run(empty_kit, servers, RunOptions())


def test_run_calls_connection_close_even_when_execution_fails(kit, servers):
    conn = _make_connection(exec_result=("", "error", 1))
    progress_mock = _make_progress_mock()

    with _patch_progress(progress_mock):
        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            sftp_instance.list_dir.return_value = []
            MockSftp.return_value = sftp_instance

            runner = RemoteRunner(connection_factory=lambda host: conn)
            results = runner.run(kit, servers, RunOptions())

    conn.close.assert_called_once()
    assert results[0].success is False


def test_run_calls_connection_close_when_connection_factory_raises(kit, servers):
    closed = []

    class FailingConn:
        def exec_command(self, cmd):
            raise RuntimeError("SSH error")

        def open_sftp(self):
            raise RuntimeError("SFTP error")

        def close(self):
            closed.append(True)

    def bad_factory(host):
        conn = FailingConn()
        return conn

    progress_mock = _make_progress_mock()

    with _patch_progress(progress_mock):
        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            MockSftp.side_effect = RuntimeError("SFTP error")
            runner = RemoteRunner(connection_factory=bad_factory)
            results = runner.run(kit, servers, RunOptions())

    assert results[0].success is False
    assert len(closed) == 1


def test_run_returns_result_per_host(kit, multi_servers):
    def factory(host):
        return _make_connection()

    progress_mock = _make_progress_mock()

    with _patch_progress(progress_mock):
        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            sftp_instance.list_dir.return_value = []
            MockSftp.return_value = sftp_instance

            runner = RemoteRunner(connection_factory=factory)
            results = runner.run(kit, multi_servers, RunOptions())

    assert len(results) == 2
    assert {r.host for r in results} == {"host1", "host2"}


def test_ssh_connection_error_returns_failed_run_result(kit, servers):
    """connection_factory raising SSHConnectionError returns RunResult(success=False) without propagating."""
    def failing_factory(host):
        raise SSHConnectionError("Auth failed")

    progress_mock = _make_progress_mock()

    with _patch_progress(progress_mock):
        runner = RemoteRunner(connection_factory=failing_factory)
        results = runner.run(kit, servers, RunOptions())

    assert len(results) == 1
    result = results[0]
    assert result.success is False
    assert "Auth failed" in result.stderr


def test_remote_dir_uses_kit_name_not_file_path_directory():
    """Remote directory must be derived from kit.name, not from the local file path parent."""
    kit = KitPipeline(
        name="kubernetes",
        uploads=["/tmp/kits/kubernetes/scripts/install_kubernetes.sh"],
        pipeline=["/tmp/kits/kubernetes/scripts/install_kubernetes.sh"],
    )
    servers = ServerGroup(user="admin", port=22, hosts=["10.0.0.1"])

    conn = _make_connection()
    runner = RemoteRunner(connection_factory=lambda host: conn)
    progress_mock = _make_progress_mock()

    with _patch_progress(progress_mock):
        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            sftp_instance.list_dir.return_value = []
            MockSftp.return_value = sftp_instance

            results = runner.run(kit, servers, RunOptions())

    assert results[0].success is True
    # The upload destination must be under .ikctl/kubernetes/, not .ikctl/scripts/
    call_args = sftp_instance.upload.call_args[0]
    assert call_args[1] == ".ikctl/kubernetes/install_kubernetes.sh", (
        f"Expected '.ikctl/kubernetes/install_kubernetes.sh', got '{call_args[1]}'"
    )
    # The pipeline command must cd into .ikctl/kubernetes/, not .ikctl/scripts/
    executed_cmd = conn.exec_command.call_args[0][0]
    assert "cd .ikctl/kubernetes;" in executed_cmd, (
        f"Expected 'cd .ikctl/kubernetes;' in command, got '{executed_cmd}'"
    )


def test_upload_prints_ok_line(kit, servers):
    """Upload success prints a line containing 'UPLOAD' and 'OK' only with debug=True."""
    conn = _make_connection()
    runner = RemoteRunner(connection_factory=lambda host: conn)
    progress_mock = _make_progress_mock()

    with _patch_progress(progress_mock):
        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            sftp_instance.list_dir.return_value = []
            MockSftp.return_value = sftp_instance

            runner.run(kit, servers, RunOptions(debug=True))

    output = _printed_text(progress_mock)
    assert "UPLOAD" in output
    assert "OK" in output


def test_run_prints_ok_line(kit, servers):
    """Pipeline step with exit_code=0 prints a line containing 'RUN' and 'OK'."""
    conn = _make_connection(exec_result=("some output", "", 0))
    runner = RemoteRunner(connection_factory=lambda host: conn)
    progress_mock = _make_progress_mock()

    with _patch_progress(progress_mock):
        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            sftp_instance.list_dir.return_value = []
            MockSftp.return_value = sftp_instance

            runner.run(kit, servers, RunOptions())

    output = _printed_text(progress_mock)
    assert "RUN" in output
    assert "OK" in output


def test_run_prints_failed_line(kit, servers):
    """Pipeline step with exit_code!=0 prints a line containing 'RUN' and 'FAILED'."""
    conn = _make_connection(exec_result=("", "error occurred", 1))
    runner = RemoteRunner(connection_factory=lambda host: conn)
    progress_mock = _make_progress_mock()

    with _patch_progress(progress_mock):
        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            sftp_instance.list_dir.return_value = []
            MockSftp.return_value = sftp_instance

            runner.run(kit, servers, RunOptions())

    output = _printed_text(progress_mock)
    assert "RUN" in output
    assert "FAILED" in output


def test_stderr_shown_on_failure_without_debug(kit, servers):
    """When a step fails without --stderr flag, stderr lines are NOT printed."""
    conn = _make_connection(exec_result=("", "permission denied\nbad exit", 1))
    runner = RemoteRunner(connection_factory=lambda host: conn)
    progress_mock = _make_progress_mock()

    with _patch_progress(progress_mock):
        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            sftp_instance.list_dir.return_value = []
            MockSftp.return_value = sftp_instance

            runner.run(kit, servers, RunOptions(debug=False, stderr_output=False))

    output = _printed_text(progress_mock)
    assert "permission denied" not in output
    assert "bad exit" not in output


def test_stderr_shown_with_stderr_flag(kit, servers):
    """When a step fails with stderr_output=True, stderr lines appear in console output."""
    conn = _make_connection(exec_result=("", "permission denied\nbad exit", 1))
    runner = RemoteRunner(connection_factory=lambda host: conn)
    progress_mock = _make_progress_mock()

    with _patch_progress(progress_mock):
        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            sftp_instance.list_dir.return_value = []
            MockSftp.return_value = sftp_instance

            runner.run(kit, servers, RunOptions(stderr_output=True))

    output = _printed_text(progress_mock)
    assert "permission denied" in output
    assert "bad exit" in output


def test_no_stdout_without_stdout_flag(kit, servers):
    """Without stdout_output=True, host command stdout does NOT appear in console output."""
    conn = _make_connection(exec_result=("host_specific_output_line", "", 0))
    runner = RemoteRunner(connection_factory=lambda host: conn)
    progress_mock = _make_progress_mock()

    with _patch_progress(progress_mock):
        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            sftp_instance.list_dir.return_value = []
            MockSftp.return_value = sftp_instance

            runner.run(kit, servers, RunOptions(stdout_output=False, debug=False))

    output = _printed_text(progress_mock)
    assert "host_specific_output_line" not in output


def test_stdout_shown_with_stdout_flag(kit, servers):
    """With stdout_output=True, host command stdout appears in console output."""
    conn = _make_connection(exec_result=("host_specific_output_line", "", 0))
    runner = RemoteRunner(connection_factory=lambda host: conn)
    progress_mock = _make_progress_mock()

    with _patch_progress(progress_mock):
        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            sftp_instance.list_dir.return_value = []
            MockSftp.return_value = sftp_instance

            runner.run(kit, servers, RunOptions(stdout_output=True))

    output = _printed_text(progress_mock)
    assert "host_specific_output_line" in output


def test_stdout_lines_prefixed_with_host_label():
    """Stdout lines from a pipeline step are prefixed with the host label, not indented."""
    kit = KitPipeline(
        name="mykit",
        uploads=["/local/kits/mykit/script.sh"],
        pipeline=["/local/kits/mykit/script.sh"],
    )
    servers = ServerGroup(user="admin", port=22, hosts=["10.30.0.53"])
    conn = _make_connection(exec_result=("hello from host", "", 0))
    runner = RemoteRunner(connection_factory=lambda host: conn)
    progress_mock = _make_progress_mock()

    with _patch_progress(progress_mock):
        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            sftp_instance.list_dir.return_value = []
            MockSftp.return_value = sftp_instance

            runner.run(kit, servers, RunOptions(stdout_output=True))

    # Collect individual printed strings as separate lines
    printed_args = [str(c[0][0]) for c in progress_mock.console.print.call_args_list if c[0]]
    stdout_lines = [s for s in printed_args if "hello from host" in s]
    assert stdout_lines, "Expected at least one stdout output line"
    for line in stdout_lines:
        assert "[10.30.0.53]" in line, (
            f"Expected '[10.30.0.53]' in line, got: {line!r}"
        )


def test_label_uses_host_ip():
    """Output lines always use the host IP as the label regardless of options.name."""
    kit = KitPipeline(
        name="mykit",
        uploads=["/local/kits/mykit/script.sh"],
        pipeline=["/local/kits/mykit/script.sh"],
    )
    servers = ServerGroup(user="admin", port=22, hosts=["10.0.0.1"])
    conn = _make_connection(exec_result=("output", "", 0))
    runner = RemoteRunner(connection_factory=lambda host: conn)
    progress_mock = _make_progress_mock()

    with _patch_progress(progress_mock):
        with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
            sftp_instance = MagicMock()
            sftp_instance.list_dir.return_value = []
            MockSftp.return_value = sftp_instance

            runner.run(kit, servers, RunOptions(name="my-group"))

    printed_args = [str(c[0][0]) for c in progress_mock.console.print.call_args_list if c[0]]
    lines_with_run = [s for s in printed_args if "RUN" in s]
    assert lines_with_run, "Expected at least one RUN output line"
    for line in lines_with_run:
        assert "[10.0.0.1]" in line, f"Expected '[10.0.0.1]' in line, got: {line!r}"
