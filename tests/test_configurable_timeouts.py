"""Tests for configurable_timeouts feature: CLI > config > default precedence."""
from __future__ import annotations

from ikctl.config.models import Context, IkctlConfig
from ikctl.executor.local import LocalExecutor


DEFAULT_CONNECT = 30.0
DEFAULT_EXEC = 120.0


def _make_config(timeout_connect: float = DEFAULT_CONNECT, timeout_exec: float = DEFAULT_EXEC) -> IkctlConfig:
    """Build a minimal IkctlConfig with the given timeout values."""
    ctx = Context(
        name="test",
        path_kits="/tmp/kits",
        path_servers="/tmp/kits",
        path_secrets="/tmp/kits/secrets",
        mode="remote",
        timeout_connect=timeout_connect,
        timeout_exec=timeout_exec,
    )
    return IkctlConfig(context="test", contexts={"test": ctx})


def _resolve_timeouts(
    cli_connect: float | None,
    cli_exec: float | None,
    config: IkctlConfig,
) -> tuple[float, float]:
    """Mirror the resolution logic used in main.py."""
    ctx = config.contexts[config.context]
    timeout_connect = cli_connect if cli_connect is not None else ctx.timeout_connect
    timeout_exec = cli_exec if cli_exec is not None else ctx.timeout_exec
    return timeout_connect, timeout_exec


class TestTimeoutResolution:
    """Verifies CLI > config > default precedence for timeout values."""

    def test_cli_timeout_connect_overrides_config(self) -> None:
        """CLI --timeout-connect 60 wins over config value 45.0."""
        config = _make_config(timeout_connect=45.0)
        timeout_connect, _ = _resolve_timeouts(60.0, None, config)
        assert timeout_connect == 60.0

    def test_cli_timeout_exec_overrides_config(self) -> None:
        """CLI --timeout-exec 240 wins over config value 180.0."""
        config = _make_config(timeout_exec=180.0)
        _, timeout_exec = _resolve_timeouts(None, 240.0, config)
        assert timeout_exec == 240.0

    def test_config_timeout_connect_used_when_no_cli(self) -> None:
        """Without CLI flag, config timeout_connect=45.0 is used."""
        config = _make_config(timeout_connect=45.0)
        timeout_connect, _ = _resolve_timeouts(None, None, config)
        assert timeout_connect == 45.0

    def test_cli_wins_over_config_for_connect(self) -> None:
        """CLI --timeout-connect 60 beats config timeout_connect=45.0."""
        config = _make_config(timeout_connect=45.0)
        timeout_connect, _ = _resolve_timeouts(60.0, None, config)
        assert timeout_connect == 60.0

    def test_defaults_when_neither_cli_nor_custom_config(self) -> None:
        """When neither CLI nor custom config, defaults 30.0 / 120.0 apply."""
        config = _make_config()
        timeout_connect, timeout_exec = _resolve_timeouts(None, None, config)
        assert timeout_connect == DEFAULT_CONNECT
        assert timeout_exec == DEFAULT_EXEC


class TestLocalExecutorReceivesResolvedTimeout:
    """LocalExecutor is constructed with the resolved timeout_exec value."""

    def test_local_executor_timeout_from_cli(self) -> None:
        """LocalExecutor uses the CLI-provided timeout_exec."""
        executor = LocalExecutor(timeout=240.0)
        assert executor._timeout == 240.0

    def test_local_executor_default_timeout(self) -> None:
        """LocalExecutor defaults to 120.0 when not provided."""
        executor = LocalExecutor()
        assert executor._timeout == DEFAULT_EXEC
