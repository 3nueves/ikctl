# Technical Design — smart_upload

## Overview

Añadir verificación de checksum SHA256 antes de subir cada archivo vía SFTP.
El checksum local se calcula con `hashlib.sha256()`. El checksum remoto se
obtiene ejecutando `sha256sum <remote_path>` vía `IConnection.exec_command()`.
Si coinciden, se salta la subida.

`SftpTransfer` necesita acceso a `IConnection.exec_command()` para obtener el
checksum remoto. Para ello, guarda la referencia a `IConnection` recibida en el
constructor (hoy solo guarda `self._sftp`).

## Classes / Interfaces affected

### SftpTransfer (`ikctl/transfer/sftp.py`)

- **Cambio:** el constructor guarda `self._connection: IConnection` además de `self._sftp`
- **Nuevo método público:** `smart_upload(local_path, remote_path, force=False) → bool`
  Retorna `True` si se subió, `False` si se saltó por unchanged.
  - Si `force=True` → sube siempre (equivalente a `upload()` actual)
  - Si `force=False`:
    1. Calcula SHA256 local con `hashlib.sha256()`
    2. Verifica si remoto existe con `self._sftp.lstat(remote_path)` (no lanza si no existe)
    3. Si existe, ejecuta `sha256sum <remote_path>` vía `self._connection.exec_command()`
       y parsea el resultado
    4. Si coincide → log + retorno `False`
    5. Si no coincide o no existe → `self._sftp.put()` + retorno `True`
- **Sin cambio:** `upload()` existente se mantiene por compatibilidad

```python
class SftpTransfer:
    def __init__(self, connection: IConnection) -> None:
        self._connection = connection
        self._sftp = connection.open_sftp()
        self._logger = logging.getLogger(__name__)

    def smart_upload(self, local_path: str, remote_path: str, force: bool = False) -> bool:
        """Upload only if changed. Returns True if uploaded, False if skipped."""
        if force:
            self._sftp.put(local_path, remote_path)
            return True

        local_hash = self._sha256(local_path)
        remote_hash = self._remote_sha256(remote_path)

        if remote_hash is not None and local_hash == remote_hash:
            self._logger.info("SKIP %s (unchanged)", remote_path)
            return False

        self._sftp.put(local_path, remote_path)
        return True

    @staticmethod
    def _sha256(path: str) -> str:
        """Return hex SHA256 of a local file."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def _remote_sha256(self, path: str) -> str | None:
        """Return hex SHA256 of a remote file, or None if it doesn't exist."""
        try:
            self._sftp.lstat(path)
        except FileNotFoundError:
            return None
        stdout, _, exit_code = self._connection.exec_command(f"sha256sum {path}")
        if exit_code != 0:
            return None
        return stdout.split()[0]
```

### RemoteRunner (`ikctl/runner/remote.py`)

- **Cambio:** en `_run_on_host()`, sustituir `sftp.upload(local_path, remote_path)`
  por `sftp.smart_upload(local_path, remote_path, force=options.force_upload)`
- Mostrar `SKIP` o `UPLOAD` en consola según el valor retornado

```python
uploaded = sftp.smart_upload(local_path, remote_path, force=options.force_upload)
if uploaded:
    progress.console.print(f"... UPLOAD  {fname:<40} [green]OK[/green]")
else:
    progress.console.print(f"... SKIP    {fname:<40} [yellow]unchanged[/yellow]")
```

### RunOptions (`ikctl/runner/base.py`)

- **Nuevo campo:** `force_upload: bool = False`

### main.py

- **Nuevo flag:** `--force-upload` (`action="store_true"`, `default=False`)
- Pasar a `RunOptions(force_upload=args.force_upload, ...)`

### DryRunRunner (`ikctl/runner/dry_run.py`)

- Mostrar `[DRY RUN] SKIP  <remote> (unchanged)` si se simula smart_upload
- Mostrar `[DRY RUN] UPLOAD: <local> → <remote>` si se simula subida
- Como dry-run no ejecuta comandos remotos, siempre muestra `UPLOAD` (no puede
  saber si el remoto existe sin conexión real)

## Data flow

```
main.py (--force-upload flag)
  → RunOptions.force_upload
    → RemoteRunner._run_on_host()
      → SftpTransfer.smart_upload(local, remote, force)
        1. hashlib.sha256() → local_hash
        2. sftp.lstat(remote) → existe?
        3. No → put() → True
        4. Sí → exec_command("sha256sum remote") → remote_hash
        5. Coinciden? → False (skip)
        6. No coinciden → put() → True
```

## Decisions & trade-offs

| Decision | Alternatives considered | Reason |
|----------|------------------------|--------|
| SHA256 en `SftpTransfer` | En `RemoteRunner` | Mantiene SRP: la lógica de transferencia está en el módulo de transferencia |
| `IConnection.exec_command` para checksum remoto | `paramiko.SFTPClient.file().read()` + hash local | `sha256sum` en remoto es más eficiente que transferir el archivo completo para hashearlo localmente |
| `lstat()` para check de existencia | `stat()` | `lstat()` no sigue symlinks; comportamiento más predecible |
| `hashlib.sha256()` (stdlib) | `hashlib.md5()` | Sin nueva dependencia; SHA256 es estándar y suficiente |
| DryRun siempre muestra UPLOAD | DryRun simula checksum | Sin conexión real no se puede saber el estado remoto; mejor subestimar el skip |
| Guardar `IConnection` en `SftpTransfer` | Inyectar solo `exec_command` | Más simple; `IConnection` ya es una abstracción; no se rompe ningún test existente |

## Risks

- `sha256sum` debe existir en el host remoto (prácticamente universal en Linux).
  En hosts sin `sha256sum`, el comando fallará con exit_code != 0 y se subirá el
  archivo (comportamiento seguro: falsos negativos, no falsos positivos).
- Si el remote_path contiene espacios, `sha256sum remote path` fallará. Los
  remote_paths generados por `RemoteRunner` no contienen espacios.
