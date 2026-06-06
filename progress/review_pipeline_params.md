# Review — feature 17 (pipeline_params)

**Verdict:** APPROVED

## Checkpoints

- C1: [x] `./init.sh` finishes with `[OK] Entorno listo`
- C2: [x] All 204 tests pass — 4 new tests in `tests/test_output_interpolator.py`, 0 regressions
- C3: [x] Names follow conventions: `snake_case` for functions/variables (`pipeline_params`, `_resolve_param_ref`, `_resolve_step_ref`), `PascalCase` for classes
- C4: [x] Logging via `self._logger = logging.getLogger(__name__)` in `OutputInterpolator` and `OrchestrationRunner`; no internal `print()`; module-level `logging.warning(...)` used correctly in `main.py` for the warning about malformed params
- C5: [x] `ConfigError` raised with clear message including `-p KEY=<value>` hint; `main.py` catches it and calls `sys.exit(1)` with a user-facing message
- C6: [x] No SSH/SFTP touched by this feature; not applicable
- C7: [x] Four new tests cover: happy path `{{ params.KEY }}`, missing key with empty dict, mixed `{{ steps.id.KEY }}` + `{{ params.KEY }}`, and `pipeline_params=None` raises `ConfigError`
- C8: [x] Tests are plain `def test_*` functions with `@pytest.fixture` — no `unittest.TestCase` inheritance
- C9: [x] Change is confined to `ikctl/orchestration/interpolator.py`, `ikctl/orchestration/runner.py`, and `ikctl/main.py`; no layer violations
- C10: [x] No new external dependencies added
- C11: [x] All acceptance criteria verified:
  - `ikctl --pipeline ... -p KEY=VALUE` is parsed in `main.py` lines 243-252 via `str.partition("=")`
  - Items without `=` trigger `logging.warning(...)` and are ignored
  - `OutputInterpolator.interpolate()` accepts `pipeline_params: dict[str, str] | None = None` (line 35)
  - `{{ params.KEY }}` resolved via `_PARAMS_PATTERN` in two-pass resolution (lines 50-54)
  - Missing key or `pipeline_params=None` raises `ConfigError` with message `"Pipeline param '{key}' not defined. Pass it with -p {key}=<value>"` (lines 88-91)
  - `OrchestrationRunner.run()` accepts and passes `pipeline_params` to `interpolator.interpolate()` (lines 55, 91-93)
  - `tests/test_output_interpolator.py` has 4 new tests: `test_interpolate_params_key`, `test_interpolate_params_key_missing`, `test_interpolate_mixed_steps_and_params`, `test_interpolate_params_none_raises_on_reference`

## Relevant files

- `/Users/davidmoyalopez/git/gitlab/invisiblebits/tooling/ikctl/ikctl/orchestration/interpolator.py`
- `/Users/davidmoyalopez/git/gitlab/invisiblebits/tooling/ikctl/ikctl/orchestration/runner.py`
- `/Users/davidmoyalopez/git/gitlab/invisiblebits/tooling/ikctl/ikctl/main.py`
- `/Users/davidmoyalopez/git/gitlab/invisiblebits/tooling/ikctl/tests/test_output_interpolator.py`
