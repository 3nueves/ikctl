# Current session

> Update this file while working, not at the end.

## Feature in progress

- **id:** 31
- **name:** strict_mode
- **type:** feature
- **started:** 2026-06-15

## Plan

1. Add `strict: bool = False` to `RunOptions` dataclass in `ikctl/runner/base.py`.
2. Add `--strict` flag to argparse in `ikctl/main.py` and wire into `RunOptions`.
3. Update `_build_remote_command()` in `ikctl/runner/remote.py` to use `bash -eo pipefail` when `options.strict` is True.
4. Create `tests/test_strict_mode.py` with all acceptance criteria tests.
5. Run `uv run pytest tests/test_strict_mode.py -v` and `uv run pytest tests -q --tb=no` — all green.

## Blocks

None.
