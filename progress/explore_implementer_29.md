# Implementer report — bugfix id=29: fix_config_error_traceback

## Files modified

- `/Users/davidmoyalopez/git/gitlab/invisiblebits/tooling/ikctl/ikctl/main.py`
  Lines ~202-208: wrapped `data.load_config_file_servers()` in `try/except ConfigError`. When `ConfigError` is raised, prints the message to stderr and exits with code 1.

## Files created

- `/Users/davidmoyalopez/git/gitlab/invisiblebits/tooling/ikctl/tests/test_config_error_handling.py`
  3 tests, all written BEFORE the fix (confirmed failing), then passing after:
  - `test_load_config_file_servers_config_error_exits_1` — exit code is 1
  - `test_load_config_file_servers_config_error_stderr_message` — message "servers config not found" appears in stderr
  - `test_load_config_file_servers_config_error_no_traceback` — "Traceback" does not appear in stdout or stderr

## Pytest result

273 passed, 1 warning in 0.70s (all tests green)

## init.sh result

Tests: 273 passed (green).
init.sh validation step 3 reports [FAIL] because there are 2 features in_progress (id=27 was already in_progress before this session — pre-existing state, not introduced by this bugfix).

## Fix summary

One-line change in `main.py`: `load_config_file_servers()` is now wrapped in `try/except ConfigError`. The exception prints `Error: <message>` to stderr and exits 1. No refactoring, no additional changes.
