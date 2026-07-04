# Implementer result: fix_rsa_sha1_compat (Transport-direct refactor)

## Status: done — pending reviewer

## What was done

### ikctl/connection/ssh.py

Rewrote `SSHConnection._connect()` to use `paramiko.Transport` directly instead of `SSHClient.connect()`.

Key changes:
- Step 1: creates a raw TCP socket via `socket.create_connection()` (or `paramiko.ProxyCommand` when `proxy_command` is set). Network errors are caught here and raised as `SSHConnectionError`.
- Step 2: instantiates `paramiko.Transport(sock)` and prepends `"ssh-rsa"` to `transport._preferred_pubkeys` if not already present — this happens BEFORE `start_client()`, so the SHA-1 algorithm is available during negotiation without any retry.
- Step 3: calls `transport.start_client(timeout=opts.banner_timeout)`. `SSHException` is caught and re-raised as `SSHConnectionError`.
- Step 4: verifies the host key against the configured policy. `RejectPolicy` path loads system host keys and calls `policy.missing_host_key()` manually. `AutoAddPolicy` and `WarningPolicy` accept without verification.
- Step 5: authenticates using the first configured method in priority order: `key_filename` (via `paramiko.PKey.from_private_key_file` which auto-detects key type), `pkey`, `password`, SSH agent (iterating all agent keys), or raises `AuthenticationException` if nothing is configured. Auth errors are caught and re-raised as `SSHConnectionError`.
- Step 6: sets keepalive on the transport if `keepalive_interval > 0`.
- Step 7: wraps the transport in a `paramiko.SSHClient` by assigning `client._transport = transport`, preserving the `exec_command` / `open_sftp` interface used by the rest of the codebase.

Removed: the inner retry block (`try/except` around `client.connect()` that detected "pubkey algorithm" in the error message and retried with `disabled_algorithms`).

### tests/test_ssh_connection.py

Removed three tests that validated the retry approach:
- `test_rsa_sha1_retry_succeeds`
- `test_rsa_sha1_retry_both_fail`
- `test_rsa_sha1_retry_on_invalid_key_exception`

Added/updated tests (13 total, all green):
- `test_connect_with_key_filename` — verifies `transport.auth_publickey` is called with the loaded key.
- `test_connect_with_password` — verifies `transport.auth_password` is called.
- `test_ssh_rsa_added_to_preferred_pubkeys` — captures `_preferred_pubkeys` at the moment `start_client()` is called; asserts `"ssh-rsa"` is the first element.
- `test_ssh_rsa_not_duplicated_if_already_present` — asserts `"ssh-rsa"` appears only once when already in the list.
- `test_close_closes_ssh_and_sftp` — behavior unchanged.
- `test_exec_command_returns_stdout_stderr_exit_code` — behavior unchanged.
- `test_keepalive_interval_calls_set_keepalive` — now checks `transport.set_keepalive()` directly.
- `test_proxy_command_creates_proxy_command_socket` — verifies `socket.create_connection` is NOT called when `proxy_command` is set.
- `test_oserror_raises_ssh_connection_error` — `socket.create_connection` raises `OSError`.
- `test_authentication_exception_raises_ssh_connection_error` — `transport.auth_password` raises `AuthenticationException`.
- `test_ssh_negotiation_failure_raises_ssh_connection_error` — `transport.start_client` raises `SSHException`.
- `test_timeout_raises_ssh_connection_error` — `socket.create_connection` raises `TimeoutError`.
- `test_no_auth_method_raises_ssh_connection_error` — no password, no key, no pkey, `allow_agent=False`.

## Verification

- `uv run pytest tests -v`: 275 passed, 0 failed.
- `./init.sh`: finished with `[OK] Entorno listo`.
