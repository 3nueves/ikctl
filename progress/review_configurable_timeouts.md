# Review — feature 6: configurable_timeouts

**Verdict:** APPROVED

## Checkpoints

- C1: [x] `./init.sh` terminates with `[OK] Entorno listo`
- C2: [x] All 77 tests pass (9 new in `tests/test_configurable_timeouts.py`, 68 pre-existing)
- C3: [x] Names follow conventions: `timeout_connect`, `timeout_exec` (snake_case fields); `load_timeout_connect`, `load_timeout_exec` (snake_case methods); `DEFAULT_CONNECT`, `DEFAULT_EXEC` (UPPER_SNAKE constants in test file)
- C4: [x] Internal layers use `logging.getLogger(__name__)`; no `print()` in config/executor layers
- C5: [x] Errors surface via domain exceptions; `main.py` and `Pipeline` handle them with `sys.exit()`
- C6: [x] New tests do not touch SSH/SFTP; they test model construction and resolution logic directly
- C7: [x] `TestTimeoutResolution` covers 5 precedence cases; `TestSSHOptionsReceivesResolvedTimeout` and `TestLocalExecutorReceivesResolvedTimeout` each cover happy path and default path
- C8: [x] Tests use `class Test*` without `unittest.TestCase` inheritance; fixtures not needed here (inline setup)
- C9: [x] Changes respect layering: `models.py` (data), `loader.py` (config), `config.py` (facade), `main.py` (CLI entry); no cross-layer violations
- C10: [x] No new external dependencies introduced
- C11: [x] All acceptance criteria satisfied (verified below)

## Acceptance criteria verification

- `main.py` accepts `--timeout-connect FLOAT` (line 76-80) and `--timeout-exec FLOAT` (line 81-86): PASS
- `Context` dataclass in `ikctl/config/models.py` has `timeout_connect: float = 30.0` (line 35) and `timeout_exec: float = 120.0` (line 36): PASS
- `ConfigLoader.load()` in `ikctl/config/loader.py` reads both fields with `ctx_data.get("timeout_connect", 30.0)` and `ctx_data.get("timeout_exec", 120.0)` (lines 51-52): PASS
- Precedence CLI > config > default implemented in `main.py` lines 110-111: `args.timeout_connect if args.timeout_connect is not None else data.load_timeout_connect()`: PASS
- `SSHOptions` receives resolved `timeout_connect` via `_build_runner` parameter at `main.py` line 43 (`timeout=timeout_connect`); no hardcoded value: PASS
- `LocalExecutor` receives resolved `timeout_exec` via `_build_runner` parameter at `main.py` line 29 (`LocalExecutor(timeout=timeout_exec)`); no hardcoded value: PASS
- Scan for `timeout=500`, `timeout=30`, `timeout=120` across `ikctl/` and `tests/`: no matches found (default values appear only as dataclass field defaults in `options.py`, `models.py`, `local.py`, which is correct — they are defaults, not hardcoded call-site values)
- `uv run ikctl --help` shows `--timeout-connect` and `--timeout-exec` with descriptions: PASS

## Notes

`test_cli_timeout_connect_overrides_config` (line 47) and `test_cli_wins_over_config_for_connect` (line 65) are functionally identical tests — both assert that CLI value 60.0 beats config value 45.0 for `timeout_connect`. This is redundant but not a blocking issue; the 5 required precedence cases are covered by the union of both tests.
