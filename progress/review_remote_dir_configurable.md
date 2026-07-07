# Review — remote_dir_configurable (Feature #33)

**Reviewer:** reviewer agent
**Date:** 2026-07-05
**Status:** APPROVED

## Verification

- [x] C1: `./init.sh` termina con `[OK] Entorno listo`
- [x] C2: Todos los tests nuevos pasan (`uv run pytest tests -v`) — 294 passed, 0 failed

## Code quality

- [x] C3: Nombres siguen convenciones: `snake_case` para funciones/variables, `PascalCase` para clases
- [x] C4: Logging via `self._logger` (obtenido con `logging.getLogger(__name__)`), no `print()` para mensajes internos
- [x] C5: Errores al usuario: mensaje claro + `sys.exit()`, nunca un stack trace crudo

## Test coverage

- [x] C6: Todo código nuevo que toca SSH/SFTP usa mocks de `unittest.mock`, no conexiones reales
- [x] C7: Cada función pública tiene al menos un test del camino feliz y uno de error
- [x] C8: Tests son funciones `def test_*` sin herencia de `unittest.TestCase`; fixtures de pytest para estado compartido

## Architecture

- [x] C9: El cambio respeta las capas definidas en `docs/architecture.md`
- [x] C10: No se añaden dependencias externas sin haberlo discutido
- [x] C11: Cada criterio de `acceptance` en `feature_list.json` se cumple y se puede demostrar

## Design adherence

- [x] `KitPipeline` has `remote_dir: str | None = None` field
- [x] `kit_repo.py` reads `kits.remote_dir` from YAML via `.get("remote_dir", None)`
- [x] `RunOptions` has `remote_dir: str | None = None` field
- [x] `main.py` accepts `--remote-dir STRING` (default None), passes to `RunOptions`
- [x] `resolve_remote_dir()` in `ikctl/runner/utils.py` implements precedence: CLI > YAML > default
- [x] `RemoteRunner._run_on_host()` uses `resolve_remote_dir()` for uploads and pipeline `cd`
- [x] `DryRunRunner.run()` uses `resolve_remote_dir()` for upload preview paths
- [x] Default `.ikctl/<kit.name>/` behavior preserved when neither CLI nor YAML set

## Files reviewed

| File | Lines | Verdict |
|------|-------|---------|
| `ikctl/config/models.py` | 28 | OK |
| `ikctl/config/kit_repo.py` | 85, 94 | OK |
| `ikctl/runner/base.py` | 28 | OK |
| `ikctl/runner/utils.py` | 1-14 (new) | OK |
| `ikctl/main.py` | 209-215, 380 | OK |
| `ikctl/runner/remote.py` | 18, 107-109 | OK |
| `ikctl/runner/dry_run.py` | 11, 43-47 | OK |
| `tests/test_remote_dir.py` | 1-115 (new) | OK |
| `tests/test_dry_run.py` | 16-21, 72 | OK |

## Notes

- No architectural violations detected
- Follows SOLID principles (SRP: resolve in runner, not in repo)
- Helper `resolve_remote_dir()` avoids code duplication between `RemoteRunner` and `DryRunRunner`
- All 294 tests pass, including 7 new tests covering every scenario
- `./init.sh` passes cleanly
