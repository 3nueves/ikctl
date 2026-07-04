# Bugfix 30b — RSA SHA-1 retry on SSHException("Invalid key")

## Status: done

## Root cause

`_connect()` in `ikctl/connection/ssh.py` only caught `paramiko.AuthenticationException` for
the "pubkey algorithm" retry path. In production, paramiko raises `paramiko.SSHException("Invalid key")`
(the parent class) instead, which bypassed the inner except and fell through to the outer handler that
converts it to `SSHConnectionError` without retrying.

## Changes

### `ikctl/connection/ssh.py`

Inner except broadened from `paramiko.AuthenticationException` to
`(paramiko.AuthenticationException, paramiko.SSHException)`.
Detection logic uses:

```python
exc_msg = str(exc)
is_pubkey_algo_error = "pubkey algorithm" in exc_msg or "Invalid key" in exc_msg
```

If neither pattern matches, the exception is re-raised unchanged so all
other `SSHException` variants (e.g. "Connection reset") still surface as
`SSHConnectionError` via the outer handler.

### `tests/test_ssh_connection.py`

Added `test_rsa_sha1_retry_on_invalid_key_exception`: first `connect()` raises
`paramiko.SSHException("Invalid key")`; second succeeds. Asserts both clients
called `connect` once each and retry kwargs contain
`{"pubkeys": ["rsa-sha2-256", "rsa-sha2-512"]}`.

## Verification

- New test confirmed FAILING before the fix (SSHConnectionError raised instead of retrying).
- After fix: 277/277 tests pass, `./init.sh` exits OK.

## Files touched

- `/Users/davidmoyalopez/git/gitlab/invisiblebits/tooling/ikctl/ikctl/connection/ssh.py`
- `/Users/davidmoyalopez/git/gitlab/invisiblebits/tooling/ikctl/tests/test_ssh_connection.py`
