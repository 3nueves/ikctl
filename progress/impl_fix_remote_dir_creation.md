# Implementation: fix_remote_dir_creation (#34)

## Date
2026-07-05

## Summary

Fixed the broken remote directory creation logic in `RemoteRunner._run_on_host()`. The old code hardcoded `.ikctl` as the parent directory regardless of the resolved `remote_dir`, causing failures for custom paths like `/opt/myapp`.

## Bug

The old code at `ikctl/runner/remote.py:111-122`:
```python
existing = sftp.list_dir(
    ".ikctl") if ".ikctl" in sftp.list_dir() else []
if kit.name not in existing:
    try:
        sftp.create_dir(".ikctl")
    except OSError:
        pass
    try:
        sftp.create_dir(remote_dir)
    except OSError:
        pass
```

Problems:
1. Hardcoded `.ikctl` — doesn't create the correct parent for custom `remote_dir` paths
2. Called `sftp.list_dir()` twice unnecessarily
3. For `/opt/myapp`, created `.ikctl` instead of `/opt` first

## Fix

Replaced with:
```python
parent = os.path.dirname(remote_dir)
if parent:
    try:
        sftp.create_dir(parent)
    except OSError:
        pass  # Already exists
try:
    sftp.create_dir(remote_dir)
except OSError:
    pass  # Already exists
```

## Tests added

- `test_remote_runner_creates_parent_dir_for_custom_remote_dir` — verifies `/opt` and `/opt/myapp` are created for `remote_dir="/opt/myapp"`
- `test_remote_runner_creates_ikctl_parent_for_default_remote_dir` — verifies `.ikctl` and `.ikctl/mykit` are created for default remote_dir

## Verification

- `uv run pytest tests -v` — 296 passed
- `./init.sh` — `[OK] Entorno listo`
