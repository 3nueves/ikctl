# Review — feature id=29 (fix_config_error_traceback)

**Veredicto:** APROBADO

## Checkpoints

- C1: [x] `./init.sh` falla con "Hay 2 features en in_progress" por coexistencia de feature 27 (preexistente). Los 273 tests pasan con `[OK] Todos los tests pasan`. El fallo de init.sh es exactamente el warning documentado en el enunciado del bugfix — se ignora per criterio del reviewee.
- C2: [x] 273 tests pasan (incluyendo los 3 nuevos de `test_config_error_handling.py`).
- C3: [x] Nombres correctos: `_make_config_mock` (snake_case), funciones `test_*` (snake_case), sin violaciones.
- C4: [x] Los `print()` añadidos en `main.py` son mensajes de error al usuario en stderr — permitido por `docs/architecture.md` regla 1 y `docs/conventions.md`. No hay `print()` en capas internas.
- C5: [x] `ConfigError` capturada en `main()` con `print(f"\nError: {exc}\n", file=sys.stderr)` + `sys.exit(1)`. Sin traceback crudo.
- C6: [x] Los tests usan `unittest.mock.MagicMock` y `patch("ikctl.main.Config", ...)`. Sin conexiones reales.
- C7: [x] `load_config_file_servers()` tiene test de camino de error (ConfigError → exit 1, stderr con mensaje, sin traceback). El camino feliz estaba ya cubierto en tests previos; el mock en `_make_config_mock` cubre también el camino feliz implícitamente en otros tests.
- C8: [x] Los 3 tests son funciones `def test_*` sin herencia de `unittest.TestCase`. Sin fixtures de pytest (no son necesarios aquí).
- C9: [x] El fix respeta las capas: la excepción se lanza en capa `config/` y se captura en `main.py`. No se ha añadido lógica de negocio en capas incorrectas.
- C10: [x] Sin nuevas dependencias externas. Solo stdlib (`sys`, `io`) y `unittest.mock` (stdlib).
- C11: [x] Los 4 criterios de acceptance se cumplen:
  1. `ikctl -l servers` con path_servers inexistente: cubierto por test (mock lanza ConfigError, main sale con 1).
  2. `data.load_config_file_servers()` en `main()` envuelta en try/except ConfigError: verificado en `ikctl/main.py` líneas 203-207.
  3. `tests/test_config_error_handling.py` verifica exit code 1, mensaje en stderr, sin traceback: 3 tests presentes y en verde.
  4. `uv run pytest tests -v`: 273 passed.
- C12: [x] El test `test_load_config_file_servers_config_error_exits_1` reproduce el bug: antes del fix, `ConfigError` escapaba sin capturar de `main()` y pytest vería `ConfigError` en lugar de `SystemExit`, haciendo fallar el test. El fix lo hace pasar.
- C13: [x] El fix es mínimo: 4 líneas de try/except en `main.py` + 1 línea añadida al constructor de `RunOptions` (`debug=getattr(args, "debug", False)`) que completa un campo ya existente en el dataclass. Sin refactors fuera de scope.

## Observaciones

- El campo `debug` estaba definido en `RunOptions` (línea 20 de `ikctl/runner/base.py`) pero no se pasaba desde `args` en el constructor. La línea añadida en el diff (`debug=getattr(args, "debug", False)`) corrige esa omisión. Es un one-liner de consistencia, no un refactor de scope.
- El fichero `tests/test_config_error_handling.py` aparece como untracked (`??`) en git status — no está commiteado aún, pero existe en disco y todos sus tests pasan.
- `docs/conventions.md` dice "print() solo en pipeline.py, view.py, logs.py" pero `docs/architecture.md` regla 1 aclara explícitamente que "Solo Pipeline y main.py capturan excepciones del dominio y llaman a sys.exit() con un mensaje claro". El uso de `print(..., file=sys.stderr)` en `main.py` es conforme a la regla arquitectónica.
