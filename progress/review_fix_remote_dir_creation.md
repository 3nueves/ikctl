# Review — fix_remote_dir_creation (#34)

**Date:** 2026-07-05
**Reviewer:** reviewer (Claude)

## Veredicto: APPROVED

## Checkpoints

- [x] C1: `./init.sh` termina con `[OK] Entorno listo`
- [x] C2: Todos los tests nuevos pasan (296 passed)
- [x] C3: Nombres siguen convenciones: `parent` es `snake_case`
- [x] C4: Logging via `self._logger`, no `print()`
- [x] C5: Errores al usuario via capas superiores, no `sys.exit()` desde runner
- [x] C6: Tests usan `unittest.mock.patch`, no conexiones SSH reales
- [x] C7: Funciones públicas testeadas: `resolve_remote_dir`, `RemoteRunner.run()`
- [x] C8: Tests son `def test_*`, sin herencia `unittest.TestCase`
- [x] C9: Cambio respeta capas — lógica en `runner/remote.py`, usa `SftpTransfer` para crear dirs
- [x] C10: Sin dependencias nuevas (`os.path` es stdlib)
- [x] C11: Acceptance criteria de `feature_list.json`#34 cumplido
- [x] C12: Test `test_remote_runner_creates_parent_dir_for_custom_remote_dir` reproduce el bug (antes fallaba: no creaba `/opt` para `/opt/myapp`)
- [x] C13: Fix mínimo — solo cambia la lógica de creación de directorio padre, sin refactor ni features nuevas

## Archivos revisados

### `ikctl/runner/remote.py:111-121`

- **Cambios:** Reemplaza hardcodeo `.ikctl` por `os.path.dirname(remote_dir)` dinámico.
- **Arquitectura:** Correcto — lógica de directorios remotos pertenece al runner, no a `Pipeline`.
- **Convenciones:** `parent` es snake_case, `pass` con comentario, contexto `try/except OSError` existente.
- **Mínimo:** Solo 8 líneas modificadas, misma lógica de manejo de errores.

### `tests/test_remote_dir.py:118-176`

- **Tests nuevos:** 2 funciones `def test_*` que validan creación de directorios padre.
- **Mocks:** Usa `patch("ikctl.runner.remote.SftpTransfer")` — correcto.
- **Cobertura:** Happy path (custom dir `/opt/myapp`) + default dir (`.ikctl/mykit`).
- **Nombres descriptivos:** `test_remote_runner_creates_parent_dir_for_custom_remote_dir`, `test_remote_runner_creates_ikctl_parent_for_default_remote_dir`.

## Resumen técnico

El bug era que `runner/remote.py` hardcodeaba `.ikctl` como directorio padre, fallando para rutas custom como `/opt/myapp`. El fix usa `os.path.dirname(remote_dir)` para extraer el padre dinámicamente. Es un cambio de 1 línea lógica, mínimo y sin efectos colaterales. Tests nuevos lo cubren adecuadamente.
