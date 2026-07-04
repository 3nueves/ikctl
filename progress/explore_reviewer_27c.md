# Review — feature 27 / RF-4 (ansible_style_output — label uses options.name)

**Verdict:** CHANGES_REQUESTED

## Verification points

### 1. Label assignment in `ikctl/runner/remote.py`

The task description states the change is:
```python
label = options.name if options.name else host
```

The actual implementation at lines 75-76 is:
```python
_raw_label = getattr(options, "name", None) or host
label = _escape_markup(f"[{_raw_label}]")
```

The logic is functionally equivalent — `options.name` is defined in `RunOptions`, so `getattr` is unnecessary (not a hard blocker), and the brackets are added via `_escape_markup(f"[{_raw_label}]")`. The label string used in `_console.print` calls is therefore `[my-group]` (escaped), which satisfies the criterion semantically.

### 2. Test `test_label_uses_options_name_when_set` (lines 275-300 of `tests/test_remote_runner.py`)

The test:
- Creates `RunOptions(name="my-group")` with `hosts=["10.0.0.1"]`.
- Asserts `"[my-group]"` appears in every UPLOAD/RUN output line.
- Asserts `"10.0.0.1"` does NOT appear in any UPLOAD/RUN line.
- The test passes.

### 3. Pre-existing format tests

`test_upload_prints_ok_line`, `test_run_prints_ok_line`, `test_run_prints_failed_line`, `test_no_stdout_without_debug`, `test_stdout_with_debug` — all 13 tests in `test_remote_runner.py` pass.

### 4. Full test suite

`uv run pytest tests -v` — **276 passed, 0 failed**.

### 5. `./init.sh` — RED

`./init.sh` exits with failure:

```
[FAIL]  Hay 2 features en in_progress (máximo 1)
[FAIL]  Entorno NO está listo. Resuelve los errores antes de avanzar.
```

`feature_list.json` has both feature 27 (`ansible_style_output`) and feature 30 (`fix_rsa_sha1_compat`) with status `in_progress` simultaneously. The harness enforces a maximum of 1 in-progress feature.

This failure is not caused by the RF-4 code change itself, but the review protocol requires `./init.sh` to finish green before approving. It does not.

### 6. Scope of change

The RF-4 change touches only `ikctl/runner/remote.py` (label derivation) and `tests/test_remote_runner.py` (new test). No other files were modified for RF-4 specifically.

## Required changes

1. In `feature_list.json`, set feature 27 (`ansible_style_output`) status to `done` (or `pending`) so that only one feature remains `in_progress`. Feature 30 is the active one per `progress/current.md`. The harness will not go green until only one feature has status `in_progress`.
