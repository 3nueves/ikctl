# Review — feature id=24 bootstrap_new_structure

**Verdict:** CHANGES_REQUESTED

## Checkpoints
- C1: [x] `./init.sh` ends with `[OK] Entorno listo`
- C2: [x] All 264 tests pass (`uv run pytest tests/ -v`)
- C3: [x] Naming follows conventions: `snake_case` methods, `PascalCase` class, `_UPPER_SNAKE` module constants
- C4: [x] `_logger = logging.getLogger(__name__)` at module level; all info calls use `_logger.info()`
- C5: [x] No `sys.exit()` in bootstrap layer; no domain errors raised either (correct — bootstrap is init-time code)
- C6: [x] No SSH/SFTP involved; not applicable
- C7: [x] All new public methods (`_ensure_secrets_file`, `_ensure_example_kit`, `_ensure_example_pipeline`) have corresponding passing tests
- C8: [x] Tests are plain `def test_*` functions using `tmp_path` fixture; no `unittest.TestCase` inheritance
- C9: [ ] `write_text()` used for all file writes — violates `docs/architecture.md` rule 4 and `docs/conventions.md` "Archivos: siempre context managers" (see below)
- C10: [x] No new external dependencies introduced
- C11: [ ] One acceptance criterion from `feature_list.json` id=24 is not fully met (see below)

## Required changes

### 1. `write_text()` violates `docs/architecture.md` rule 4 — `ikctl/config/bootstrap.py` lines 157, 165–167, 175, 187, 195

`docs/architecture.md` rule 4 states: "Toda escritura de archivo usa context manager (`with open(...) as f`)."
`docs/conventions.md` section "Archivos: siempre context managers" reiterates this pattern as the correct one.

The implementation uses `pathlib.Path.write_text()` on every file write:
- Line 157: `config_file.write_text(content, encoding="utf-8")`
- Lines 165–167: `servers_yaml.write_text(yaml.dump(...), encoding="utf-8")`
- Line 175: `secrets_file.write_text("", encoding="utf-8")`
- Line 187: `kit_file.write_text(_EXAMPLE_KIT, encoding="utf-8")`
- Line 195: `pipeline_file.write_text(_EXAMPLE_PIPELINE, encoding="utf-8")`

The feature spec (`requirements.md`, `design.md`) mandates `write_text()`, but those documents are subordinate to `docs/architecture.md`. Each of these calls must be replaced with a `with open(..., "w", encoding="utf-8") as f: f.write(...)` context manager.

Note: the test file also uses bare `open()` without context manager for reads at lines 17, 31, and 35 — those must be fixed too (`with open(...) as f`).

### 2. Acceptance criterion "El comportamiento idempotente y --force siguen funcionando" is not demonstrably covered

`feature_list.json` id=24 acceptance criterion 8 says: "El comportamiento idempotente y --force siguen funcionando (no crea si ya existe, sobreescribe con --force)". The `--force` path is handled by `InitWizard` and `requirements.md` explicitly says it is out of scope for `ConfigBootstrap`; however there is no test or documentation note confirming `--force` via `InitWizard` still routes correctly through the new directory structure (`default/kits`, `default/pipelines`, `default/servers`). The existing `test_setup_is_idempotent` covers the idempotence half. Add a comment in `test_bootstrap.py` (or a test in `tests/test_init_command.py`) confirming that `--force` on `InitWizard` writes to the same new paths, or document that this criterion is verified by `test_init_command.py::test_force_overwrites_existing_files`.
