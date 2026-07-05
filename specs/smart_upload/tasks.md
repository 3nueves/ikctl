# Implementation tasks — smart_upload

> Ordered list. Complete each task before starting the next.
> Update [ ] to [x] as you go. Document blockers in progress/current.md.

- [ ] T1: Añadir `_sha256()` y `_remote_sha256()` a `SftpTransfer`; guardar `self._connection` en el constructor
- [ ] T2: Implementar `smart_upload(local_path, remote_path, force=False) → bool` en `SftpTransfer`
- [ ] T3: Añadir `force_upload: bool = False` a `RunOptions` en `ikctl/runner/base.py`
- [ ] T4: Añadir `--force-upload` flag CLI en `main.py` y pasarlo a `RunOptions`
- [ ] T5: Modificar `RemoteRunner._run_on_host()` para usar `sftp.smart_upload()` y mostrar SKIP/UPLOAD en consola
- [ ] T6: Crear `tests/test_smart_upload.py`:
  - `test_upload_skips_when_unchanged`: mockea `exec_command` para retornar mismo hash → verifica que NO se llama a `sftp.put`
  - `test_upload_when_changed`: mockea `exec_command` para retornar hash distinto → verifica que SÍ se llama a `sftp.put`
  - `test_upload_when_remote_missing`: mockea `lstat` para lanzar `FileNotFoundError` → verifica que se sube
  - `test_force_upload_always_uploads`: con `force=True`, verifica que se sube aunque el hash coincida
  - `test_remote_exec_fallback_uploads`: mockea `exec_command` exit_code != 0 → verifica que se sube (fallback seguro)
- [ ] T7: Ejecutar `./init.sh` — debe terminar con `[OK] Entorno listo`
