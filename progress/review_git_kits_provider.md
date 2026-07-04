# Review — feature 13: git_kits_provider

**Verdict:** APPROVED

## Checkpoints

- C1: [x] `./init.sh` finishes with `[OK] Entorno listo`
- C2: [x] All 142 tests pass (6 new tests in `tests/test_git_provider.py`; all previous tests continue passing)
- C3: [x] Names follow conventions: `snake_case` for functions/variables, `PascalCase` for classes (`GitKitsProvider`, `_repo_name`, `_clone`, `_pull`, `_resolve_path_kits`)
- C4: [x] Logging via `self._logger = logging.getLogger(__name__)` in `GitKitsProvider.__init__`; no internal `print()` calls in the new module
- C5: [x] `GitKitsProvider` raises `ConfigError` with clear messages on git failure; `sys.exit()` is not called from within the layer
- C6: [x] No SSH/SFTP involved; `subprocess.run` is mocked in all 6 tests via `unittest.mock.patch("ikctl.config.git_provider.subprocess.run")`; no real git calls
- C7: [x] `ensure()` has: happy path clone (`test_ensure_clones_on_first_use`), happy path pull (`test_ensure_pulls_on_subsequent_use`), error clone (`test_ensure_raises_config_error_on_clone_failure`), error pull (`test_ensure_raises_config_error_on_pull_failure`); `_repo_name()` has determinism test and `.git` strip test
- C8: [x] Tests are plain `def test_*` functions; `tmp_path` pytest fixture used for state; no `unittest.TestCase` inheritance
- C9: [x] `GitKitsProvider` lives under `ikctl/config/` as specified in `docs/architecture.md`; import in `kit_repo.py` is a local lazy import (inside the method) to avoid circular imports, which is correct; `KitRepository._resolve_path_kits()` correctly intercepts path resolution before it reaches the filesystem layer
- C10: [x] No new external dependencies added; `subprocess` (stdlib), `hashlib` (stdlib), `pathlib` (stdlib) are the only new imports; `pyproject.toml` unchanged
- C11: [x] All 9 acceptance criteria verified:
  - `Context` dataclass has `kits_repo: str | None = None` and `kits_ref: str = "main"` — confirmed in `ikctl/config/models.py` lines 38-39
  - `ikctl/config/git_provider.py` exists with `GitKitsProvider.ensure(kits_repo, kits_ref) -> str` — confirmed
  - Clone command: `["git", "clone", kits_repo, "--branch", kits_ref, "--depth", "1", str(local_path)]` — confirmed in `git_provider.py` lines 46-48
  - Pull command: `["git", "-C", str(local_path), "pull", "origin", kits_ref]` — confirmed in `git_provider.py` lines 57-59
  - git errors raise `ConfigError` with clear message — confirmed lines 51, 62
  - `KitRepository._resolve_path_kits()` uses `GitKitsProvider` when `kits_repo` set, falls back to `context.path_kits` otherwise — confirmed in `kit_repo.py` lines 20-26
  - When `kits_repo` is not set, behavior is identical to previous (fallback to `context.path_kits`) — all prior `test_kit_repo.py` tests pass
  - Tests cover: clone, pull, `ConfigError` on clone failure, `ConfigError` on pull failure, deterministic name, `.git` strip — confirmed in `tests/test_git_provider.py`
  - `ConfigLoader.load()` reads `kits_repo` and `kits_ref` from YAML with correct defaults — confirmed in `loader.py` lines 55-56

## Additional observations

- `_repo_name()` in `git_provider.py` at line 39 uses `hashlib.sha1` without `usedforsecurity=False`. Python 3.9+ allows this argument to suppress security warnings when SHA1 is used for non-cryptographic purposes (directory naming). This is not a blocking issue since Python 3.13 still accepts `hashlib.sha1(data)` without the flag, and it is used only for path disambiguation, not for any security purpose. It is a minor style note.
- The lazy import `from ikctl.config.git_provider import GitKitsProvider` inside `_resolve_path_kits()` is intentional and correct; it avoids a potential circular import and is an accepted pattern in the codebase.
- `CACHE_DIR` is a class-level attribute (`pathlib.Path`), which the tests override cleanly via `provider.CACHE_DIR = tmp_path`.

## Changes required

None.
