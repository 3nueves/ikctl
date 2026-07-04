# Review — feature 30 (fix_rsa_sha1_compat)

**Veredicto:** CHANGES_REQUESTED

## Checkpoints

- C1: [ ] `./init.sh` falla — salida: `[FAIL] Hay 2 features en in_progress (máximo 1)`. El implementer añadió en el mismo lote tanto id=27 (`ansible_style_output`, `status: in_progress`) como id=30 (`fix_rsa_sha1_compat`, `status: in_progress`) a `feature_list.json`. Antes de este bugfix, `feature_list.json` solo tenía ids 1–26 (verificado con `git show HEAD:feature_list.json`); id=27 no era un estado preexistente, fue introducido por el propio implementer.
- C2: [x] 275 tests pasan al 100% (`uv run pytest tests -v` — 275 passed, 1 warning).
- C3: [x] Nombres correctos. `_connect()` snake_case, `SSHConnection` PascalCase, `retry_kwargs` snake_case. Constante inline `{"pubkeys": ["rsa-sha2-256", "rsa-sha2-512"]}` correcta.
- C4: [x] Logging via `self._logger.info("Retrying with ssh-rsa (SHA-1) for host %s", opts.hostname)`. Sin `print()`. Usa `%s` en lugar de f-string, que es correcto para logging.
- C5: [x] Si el reintento falla, lanza `SSHConnectionError(f"Authentication failed for {opts.hostname}: {exc}")`. Mensaje claro, sin stack trace crudo al usuario (capturado aguas arriba en `RemoteRunner`).
- C6: [x] Tests usan `unittest.mock.patch` y `MagicMock`. Sin conexiones SSH reales. `mock_client_cls.side_effect = [first_client, second_client]` controla las dos instancias de `paramiko.SSHClient`.
- C7: [x] Camino feliz: `test_rsa_sha1_retry_succeeds` — primer intento falla con "pubkey algorithm", segundo tiene éxito. Camino de error: `test_rsa_sha1_retry_both_fail` — ambos intentos fallan, se lanza `SSHConnectionError`. Adicionalmente, el test preexistente `test_authentication_exception_raises_ssh_connection_error` cubre el caso donde el mensaje NO contiene "pubkey algorithm" (la excepción se relanza sin retry).
- C8: [x] Ambos tests son funciones `def test_*` sin herencia de `unittest.TestCase`. Usan `@patch` y `pytest.raises`.
- C9: [x] El fix vive exclusivamente en `ikctl/connection/ssh.py` dentro de `_connect()`. Respeta la capa `connection/` definida en `docs/architecture.md`. No toca `Pipeline`, `Runner` ni `main.py`.
- C10: [x] Sin dependencias externas nuevas. Solo se usa `paramiko` que ya era dependencia de producción declarada.
- C11: [x] Todos los criterios de aceptación verificados:
  1. `_connect()` captura `AuthenticationException` con "pubkey algorithm" en el mensaje — `ssh.py` líneas 81-83.
  2. Reintenta con `disabled_algorithms={"pubkeys": ["rsa-sha2-256", "rsa-sha2-512"]}` — `ssh.py` línea 91.
  3. `self._logger.info("Retrying with ssh-rsa (SHA-1) for host %s", opts.hostname)` antes del reintento — `ssh.py` líneas 84-86.
  4. Si el reintento falla → `SSHConnectionError` — capturado por el `except` exterior en `ssh.py` línea 93.
  5. Si tiene éxito → conexión continúa normalmente (el cliente retornado es el `second_client`).
  6. 2 tests nuevos en `test_ssh_connection.py`: `test_rsa_sha1_retry_succeeds` y `test_rsa_sha1_retry_both_fail`.
  7. `uv run pytest tests -v` — 275 passed.
  8. `./init.sh` — FALLA (ver C1).
- C12: [x] `test_rsa_sha1_retry_succeeds` reproduce el bug: sin el fix, el primer `AuthenticationException` con "pubkey algorithm" habría sido propagado como `SSHConnectionError` directamente. Con el fix, el test verifica que `SSHConnection(opts)` no lanza excepción y que el segundo cliente fue llamado con `disabled_algorithms` correcto. Antes del fix, este test habría fallado porque `second_client.connect` no habría sido invocado.
- C13: [x] El fix es mínimo: 13 líneas añadidas en `_connect()`, solo envuelven el `client.connect(**connect_kwargs)` existente con un bloque try/except interno. Sin refactors fuera del scope.

## Verificaciones adicionales (solicitadas en el encargo)

- **Log solo via `self._logger.info`, sin `print`**: confirmado. `ssh.py` líneas 84-86. Sin ningún `print()` en el diff.
- **Si el mensaje NO contiene "pubkey algorithm" → excepción se relanza sin retry**: confirmado. `ssh.py` líneas 82-83: `if "pubkey algorithm" not in str(exc): raise`. El test preexistente `test_authentication_exception_raises_ssh_connection_error` (mensaje "Auth failed", sin "pubkey algorithm") cubre este camino y pasa.

## Cambios requeridos

1. **`feature_list.json`**: eliminar la entrada id=27 (`ansible_style_output`) del commit actual, o cambiar su `status` de `in_progress` a `pending`. El implementer introdujo id=27 con `status: in_progress` en el mismo lote que id=30, creando dos features simultáneas `in_progress`, lo que viola la regla `one_feature_at_a_time` y hace fallar `init.sh`. Solo id=30 debe estar en `in_progress`.
