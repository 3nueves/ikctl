# Review — feature 3: solid_connections

**Verdict:** APPROVED

## Checkpoints

- C1: [x] `./init.sh` ends with `[OK] Entorno listo`
- C2: [x] All 54 tests pass (10 new: 7 in `test_ssh_connection.py`, 3 in `test_sftp_transfer.py`)
- C3: [x] Names follow conventions: `snake_case` for functions/variables, `PascalCase` for classes, `I` prefix for ABCs (`IConnection`)
- C4: [x] All new modules use `logging.getLogger(__name__)` — no `print()` in `connection/` or `transfer/`
- C5: [x] No `sys.exit()` in any class under `connection/` or `transfer/`; architecture rule enforced
- C6: [x] All SSH/SFTP code tested with `unittest.mock` mocks of `paramiko.SSHClient`; no real connections
- C7: [x] Each public method has at least one happy-path test and one error/variant test
- C8: [x] Tests are `def test_*` functions; no `unittest.TestCase` inheritance; fixtures only where needed
- C9: [x] Respects layer architecture: `base.py` (ABC) → `options.py` (dataclass) → `ssh.py` (impl); `transfer/sftp.py` depends on `IConnection`, not on concrete class
- C10: [x] No new external dependencies added; only `paramiko` (already declared)
- C11: [x] All acceptance criteria from `feature_list.json` id=3 are fulfilled (see detail below)

## Acceptance criteria detail

- `ikctl/connection/base.py`: `IConnection` ABC with `exec_command(cmd: str) -> tuple[str, str, int]`, `open_sftp() -> paramiko.SFTPClient`, `close() -> None`. [x]
- `ikctl/connection/options.py`: `@dataclass SSHOptions` with all required fields: `hostname`, `port=22`, `username`, `password=None`, `passphrase=None`, `key_filename: str|list[str]|None=None`, `pkey=None`, `allow_agent=True`, `look_for_keys=True`, `timeout=30.0`, `auth_timeout=30.0`, `banner_timeout=30.0`, `channel_timeout=None`, `keepalive_interval=0`, `compress=False`, `disabled_algorithms=None`, `host_key_policy='auto_add'`, `proxy_command=None`. [x]
- `ikctl/connection/ssh.py`: `SSHConnection(IConnection)` constructor receives `SSHOptions`. [x]
- Authentication by key (`key_filename`), password, passphrase, SSH agent (`allow_agent=True`) all supported. [x]
- ProxyCommand supported: `sock=paramiko.ProxyCommand(opts.proxy_command)` when `proxy_command` is set. [x]
- `keepalive_interval > 0` calls `transport.set_keepalive()`. [x]
- `close()` uses `try/finally`; closes SFTP if open, then closes SSH client. [x] (`ssh.py` lines 99-105)
- `exec_command()` returns `(stdout: str, stderr: str, exit_code: int)`, does not print. [x] (`ssh.py` lines 85-91)
- RSA SHA1 workaround (lines 9-16 of original `connect.py`) is absent from all new `connection/` modules. [x]
- `ikctl/transfer/sftp.py` exists with `SftpTransfer` that receives `IConnection`. [x]
- `tests/test_ssh_connection.py` and `tests/test_sftp_transfer.py` all pass. [x]
- `uv run ikctl --version` returns `0.6.4` — existing code unaffected. [x]
- Type hints use Python 3.13 syntax (`str | None`, `float | None`) throughout. [x]
- No class in `connection/` calls `sys.exit()`. [x]

## Notes

- `ikctl/remote/connect.py` was intentionally left intact (still contains the RSA SHA1 workaround and the legacy `Connection` class). This is acceptable per the implementation plan: feature 4 (`solid_runners`) will refactor `remote_kits.py` and retire `connect.py`. The acceptance criteria for feature 3 only require that the workaround not be present in the new `connection/` modules — which is the case.
- `SSHOptions` is not `frozen=True`. This is acceptable: `SSHOptions` is a configuration value object but mutability does not violate any stated convention or acceptance criterion.
