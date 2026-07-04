# Review — feature 30 (fix_rsa_sha1_compat)

**Veredicto:** CHANGES_REQUESTED

## Checkpoints

- C1: [x] `./init.sh` termina con `[OK] Entorno listo`
- C2: [x] 273 tests pasan (0 fallos)
- C3: [x] Nombres siguen convenciones
- C4: [x] Logging via `self._logger`, no `print()`
- C5: [x] Errores al usuario con `sys.exit()` en las capas correctas
- C6: [x] Tests SSH usan mocks de `unittest.mock`, no conexiones reales
- C7: [x] Funciones públicas tienen tests de camino feliz y error
- C8: [x] Tests son funciones `def test_*`; fixtures de pytest para estado compartido
- C9: [x] Cambio respeta las capas de `docs/architecture.md`
- C10: [x] No se añaden dependencias externas sin discutir (se restringe paramiko a `<4.0`)
- C11: [ ] Los criterios de `acceptance` en `feature_list.json` NO se cumplen — ver detalle
- C12: [ ] No existe test que reproduzca el bug original y fallara antes del fix — ver detalle
- C13: [ ] El fix NO es mínimo; introduce un refactor mayor fuera del scope del bug — ver detalle

## Cambios requeridos

### 1. C11 — Los acceptance criteria no se cumplen

Los acceptance criteria de feature 30 en `feature_list.json` (líneas 549-556) definen:
- `SSHConnection._connect()` captura `AuthenticationException` cuyo mensaje contiene `'pubkey algorithm'`
- Al capturarla, crea nuevo `paramiko.SSHClient` y reintenta con `disabled_algorithms={'pubkeys': ['rsa-sha2-256', 'rsa-sha2-512']}`
- Antes del reintento emite `self._logger.info('Retrying with ssh-rsa (SHA-1) for host %s', hostname)`
- Si el reintento falla, lanza `SSHConnectionError`

Lo implementado en `ikctl/connection/ssh.py` es un enfoque completamente distinto: reescribir `_connect()` para usar `paramiko.Transport` directamente, sin ningún mecanismo de reintento. La restricción de versión `paramiko<4.0` en `pyproject.toml` es la única medida funcional contra el problema original.

Opciones para resolver:
  - A) Actualizar los acceptance criteria en `feature_list.json` para reflejar el enfoque real (pin de versión + Transport-direct), y añadir un test que demuestre que el código no usa `paramiko>=4.0`.
  - B) Implementar el mecanismo de reintento descrito en los acceptance criteria y añadir los tests correspondientes.

### 2. C12 — Falta test que reproduce el bug

No existe ningún test en `tests/test_ssh_connection.py` que:
- Simule que el primer intento de conexión falla por incompatibilidad de algoritmo de clave pública
- Demuestre que la solución aplicada (ya sea pin de versión o reintento) resuelve el problema

Los tests eliminados (`test_ssh_rsa_added_to_preferred_pubkeys`, `test_ssh_rsa_not_duplicated_if_already_present`) eran para el mecanismo de inyección de `_preferred_pubkeys`, que ya no existe. No se añadió ningún test que reemplazara la cobertura del escenario de bug.

### 3. C13 — El fix no es mínimo

`ikctl/connection/ssh.py` acumula 112 líneas modificadas (refactor completo de `_connect()` de `SSHClient.connect()` a `paramiko.Transport` directo). El diff incluye también cambios en `ikctl/runner/remote.py` (68 líneas) y varios archivos más, sumando 911 inserciones / 232 eliminaciones en 24 archivos bajo una sola feature de tipo bugfix.

Un bugfix debe limitarse al scope del bug. El refactor de `_connect()` al enfoque Transport-direct es un cambio de arquitectura no declarado en los acceptance criteria de feature 30. Debería ser una feature o refactor separada en `feature_list.json`.

## Estado de verificación técnica

- `pyproject.toml` línea 26: `"paramiko>=3.0,<4.0"` — correcto
- `ikctl/connection/ssh.py`: sin `_preferred_pubkeys` mutation — correcto
- `tests/test_ssh_connection.py`: sin `test_ssh_rsa_added_to_preferred_pubkeys` ni `test_ssh_rsa_not_duplicated_if_already_present` — correcto
- `uv run pytest tests -v`: 273 passed, 0 failed — correcto
- `./init.sh`: `[OK] Entorno listo` — correcto
