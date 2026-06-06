"""Tests for ssh_auth_method_selection bugfix: correct auth method is selected based on pkey/password."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from ikctl.config.models import ServerGroup
from ikctl.connection.options import SSHOptions
from ikctl.main import _build_runner


def _make_servers(
    password: str = "no_pass",
    pkey: str | None = None,
    hosts: list[str] | None = None,
) -> ServerGroup:
    """Build a minimal ServerGroup for testing."""
    return ServerGroup(
        user="admin",
        port=22,
        hosts=hosts or ["10.0.0.1"],
        password=password,
        pkey=pkey,
    )


def _make_options(dry_run: bool = False, mode: str = "remote", parallel_workers: int = 1) -> object:
    """Build a minimal options namespace for _build_runner."""

    class Opts:
        pass

    opts = Opts()
    opts.dry_run = dry_run
    opts.mode = mode
    opts.parallel_workers = parallel_workers
    return opts


class TestPkeyAuthMethodSelection:
    """When pkey is set, SSHOptions must use publickey auth exclusively."""

    def test_bug_reproduction_pkey_with_password_passes_null_password(self) -> None:
        """Reproduces the bug: pkey defined + password set must result in password=None.

        Before the fix this test FAILS because password is passed to SSHOptions
        even when pkey is defined.
        """
        servers = _make_servers(pkey="/path/to/key", password="mypassword")
        opts = _make_options()
        captured: list[SSHOptions] = []

        with patch("ikctl.main.SSHConnection") as mock_conn_cls:
            mock_conn_cls.side_effect = lambda o: captured.append(o) or MagicMock()
            runner = _build_runner(opts, servers, secrets="", timeout_connect=30.0, timeout_exec=120.0)
            runner._connection_factory("10.0.0.1")  # type: ignore[attr-defined]

        assert len(captured) == 1, "SSHConnection was not called"
        ssh_opts = captured[0]
        assert ssh_opts.password is None, (
            f"Bug: password={ssh_opts.password!r} was passed to SSHOptions even though pkey is set"
        )
        assert ssh_opts.key_filename == "/path/to/key"

    def test_pkey_defined_uses_publickey_auth(self) -> None:
        """SSHOptions receives key_filename=pkey, password=None, allow_agent=False, look_for_keys=False."""
        servers = _make_servers(pkey="/path/to/key")
        opts = _make_options()
        captured: list[SSHOptions] = []

        with patch("ikctl.main.SSHConnection") as mock_conn_cls:
            mock_conn_cls.side_effect = lambda o: captured.append(o) or MagicMock()
            runner = _build_runner(opts, servers, secrets="", timeout_connect=30.0, timeout_exec=120.0)
            runner._connection_factory("10.0.0.1")  # type: ignore[attr-defined]

        ssh_opts = captured[0]
        assert ssh_opts.key_filename == "/path/to/key"
        assert ssh_opts.password is None
        assert ssh_opts.allow_agent is False
        assert ssh_opts.look_for_keys is False

    def test_pkey_defined_ignores_password_field(self) -> None:
        """Even if servers.password is set, pkey takes priority and password=None."""
        servers = _make_servers(pkey="/path/to/key", password="secret123")
        opts = _make_options()
        captured: list[SSHOptions] = []

        with patch("ikctl.main.SSHConnection") as mock_conn_cls:
            mock_conn_cls.side_effect = lambda o: captured.append(o) or MagicMock()
            runner = _build_runner(opts, servers, secrets="", timeout_connect=30.0, timeout_exec=120.0)
            runner._connection_factory("10.0.0.1")  # type: ignore[attr-defined]

        ssh_opts = captured[0]
        assert ssh_opts.password is None
        assert ssh_opts.key_filename == "/path/to/key"


class TestPasswordAuthMethodSelection:
    """When password is set and pkey is None, SSHOptions must use password auth exclusively."""

    def test_password_defined_and_no_pkey_uses_password_auth(self) -> None:
        """SSHOptions receives password=password, key_filename=None, allow_agent=False, look_for_keys=False."""
        servers = _make_servers(password="mypassword", pkey=None)
        opts = _make_options()
        captured: list[SSHOptions] = []

        with patch("ikctl.main.SSHConnection") as mock_conn_cls:
            mock_conn_cls.side_effect = lambda o: captured.append(o) or MagicMock()
            runner = _build_runner(opts, servers, secrets="", timeout_connect=30.0, timeout_exec=120.0)
            runner._connection_factory("10.0.0.1")  # type: ignore[attr-defined]

        ssh_opts = captured[0]
        assert ssh_opts.password == "mypassword"
        assert ssh_opts.key_filename is None
        assert ssh_opts.allow_agent is False
        assert ssh_opts.look_for_keys is False


class TestNoCredentialsAuthMethodSelection:
    """When neither pkey nor password is defined, paramiko agent/key discovery is enabled."""

    def test_no_credentials_uses_agent_discovery(self) -> None:
        """SSHOptions receives allow_agent=True, look_for_keys=True, password=None."""
        servers = _make_servers(password="no_pass", pkey=None)
        opts = _make_options()
        captured: list[SSHOptions] = []

        with patch("ikctl.main.SSHConnection") as mock_conn_cls:
            mock_conn_cls.side_effect = lambda o: captured.append(o) or MagicMock()
            runner = _build_runner(opts, servers, secrets="", timeout_connect=30.0, timeout_exec=120.0)
            runner._connection_factory("10.0.0.1")  # type: ignore[attr-defined]

        ssh_opts = captured[0]
        assert ssh_opts.allow_agent is True
        assert ssh_opts.look_for_keys is True
        assert ssh_opts.password is None

    def test_secrets_used_as_password_when_no_explicit_credentials(self) -> None:
        """When servers.password='no_pass' and pkey=None, secrets is passed as password with agent=True."""
        servers = _make_servers(password="no_pass", pkey=None)
        opts = _make_options()
        captured: list[SSHOptions] = []

        with patch("ikctl.main.SSHConnection") as mock_conn_cls:
            mock_conn_cls.side_effect = lambda o: captured.append(o) or MagicMock()
            runner = _build_runner(opts, servers, secrets="vault_secret", timeout_connect=30.0, timeout_exec=120.0)
            runner._connection_factory("10.0.0.1")  # type: ignore[attr-defined]

        ssh_opts = captured[0]
        assert ssh_opts.password == "vault_secret"
        assert ssh_opts.allow_agent is True
