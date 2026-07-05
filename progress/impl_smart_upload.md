# Implementation Summary — smart_upload (feature #28)

## Changes made

### `ikctl/transfer/sftp.py`
- Constructor now saves `self._connection: IConnection` (design: guardar referencia)
- Added `smart_upload(local_path, remote_path, force=False) → bool` — uploads only if changed, returns True if uploaded, False if skipped
- Added `_sha256(path) → str` — static method, reads file in 64KB chunks, returns hex SHA256 (stdlib `hashlib.sha256`)
- Added `_remote_sha256(path) → str | None` — checks existence via `self._sftp.lstat()`, executes `sha256sum` via `self._connection.exec_command()`, returns hash or None on failure/missing

### `ikctl/runner/base.py`
- Added `force_upload: bool = False` field to `RunOptions` dataclass

### `ikctl/main.py`
- Added `--force-upload` CLI flag (`action="store_true"`, `default=False`)
- Passed `force_upload=getattr(args, "force_upload", False)` to `RunOptions`

### `ikctl/runner/remote.py`
- `_run_on_host()` now calls `sftp.smart_upload(local_path, remote_path, force=options.force_upload)` instead of `sftp.upload()`
- Always prints `UPLOAD` (green OK) or `SKIP` (yellow unchanged) per design

### `tests/test_smart_upload.py` (new, 5 tests)
- `test_upload_skips_when_unchanged`: matching hash → `put()` NOT called, returns False
- `test_upload_when_changed`: different hash → `put()` called, returns True
- `test_upload_when_remote_missing`: `lstat` raises `FileNotFoundError` → `put()` called
- `test_force_upload_always_uploads`: `force=True` → `put()` called even if hash matches
- `test_remote_exec_fallback_uploads`: `sha256sum` exit_code != 0 → `put()` called (safe fallback)

### `tests/test_remote_runner.py` (adapted)
- Updated 2 tests that checked `sftp_instance.upload` → now check `sftp_instance.smart_upload`

## Verification
- `uv run pytest tests -v`: **287 passed** (5 new, 2 adapted, 280 existing)
- `./init.sh`: **[OK] Entorno listo**

## Feature status
Not marked as `done` — pending human review.
