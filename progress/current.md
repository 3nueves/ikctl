# Current session

> Update this file while working, not at the end.

## Feature in progress

- **id:** 28
- **name:** smart_upload
- **type:** feature
- **started:** 2026-07-05

## Plan

1. Modificar `SftpTransfer` (sftp.py): guardar `self._connection`, añadir `smart_upload()`, `_sha256()`, `_remote_sha256()`
2. Añadir `force_upload: bool = False` a `RunOptions` en `runner/base.py`
3. Añadir `--force-upload` flag en `main.py` y pasarlo a `RunOptions`
4. Modificar `RemoteRunner._run_on_host()` para usar `sftp.smart_upload()` y mostrar SKIP/UPLOAD
5. Crear `tests/test_smart_upload.py` con 5 tests (mockeando sin conexiones reales)
6. Verificar con `uv run pytest tests -v` y `./init.sh`

## Blocks

None.
