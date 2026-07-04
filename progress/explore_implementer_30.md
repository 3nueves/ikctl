# Implementer summary: fix_rsa_sha1_compat (id=30)

## Files modified

- `ikctl/connection/ssh.py`: Added retry logic inside `_connect()`. The original
  `client.connect(**connect_kwargs)` call is now wrapped in a nested try/except
  that catches `paramiko.AuthenticationException`. If the exception message
  contains `"pubkey algorithm"`, the code logs an info message, closes the first
  client, creates a new `paramiko.SSHClient`, and retries with
  `disabled_algorithms={"pubkeys": ["rsa-sha2-256", "rsa-sha2-512"]}`. If the
  retry also raises an exception it falls through to the outer except block and
  becomes `SSHConnectionError`. Non-pubkey-algorithm `AuthenticationException`
  values are re-raised immediately.

- `tests/test_ssh_connection.py`: Two new tests appended without removing any
  existing tests:
  - `test_rsa_sha1_retry_succeeds`: first `connect()` raises
    `AuthenticationException` with "pubkey algorithm"; second (with
    `disabled_algorithms`) succeeds. Verifies no exception is raised and
    `disabled_algorithms` is set correctly on the retry call.
  - `test_rsa_sha1_retry_both_fail`: both `connect()` calls raise
    `AuthenticationException` with "pubkey algorithm"; verifies
    `SSHConnectionError` is raised.

## Test results

```
275 passed, 1 warning in 0.68s
```

All pre-existing tests continued to pass. Both new tests pass after the fix.

## init.sh result

Tests passed 100%. The only init.sh failure is a pre-existing condition: both
feature 27 (ansible_style_output) and feature 30 (fix_rsa_sha1_compat) are
`in_progress` simultaneously in `feature_list.json`, which violates the
"maximum 1 in_progress" rule. Feature 27 was already in that state before this
session started and is outside the scope of this bugfix.
