# RF-4 Implementation: label uses options.name

## Status: done

## Changes made

### ikctl/runner/remote.py

- Added `from rich.markup import escape as _escape_markup` import.
- Changed `label = host` to:
  ```python
  _raw_label = getattr(options, "name", None) or host
  label = _escape_markup(f"[{_raw_label}]")
  ```
- Updated all 5 `_console.print` calls that used `f"[{label}] ..."` to use `f"{label} ..."` since `label` now already contains the escaped bracket expression.

Key detail: Rich markup treats `[my-group]` as a tag and strips it from output. Using `_escape_markup` on the full `[raw_label]` expression produces `\[my-group]` which Rich renders as the literal text `[my-group]`. Using `getattr(options, "name", None)` avoids `AttributeError` when a test passes a plain `object()` as options.

### tests/test_remote_runner.py

Added `test_label_uses_options_name_when_set`:
- Creates `RunOptions(name="my-group")` with host `10.0.0.1`.
- Asserts that UPLOAD and RUN output lines contain `[my-group]` and do not contain the host IP.

## Verification

- `uv run pytest tests -v`: 276 passed, 0 failed.
- `./init.sh`: all checks pass except the pre-existing `in_progress` count constraint (2 features in_progress, unrelated to this change).
