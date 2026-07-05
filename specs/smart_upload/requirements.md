# Requirements — smart_upload

## Functional requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| R1 | `SftpTransfer.smart_upload(local_path, remote_path)` calcula SHA256 del fichero local | High |
| R2 | Si el fichero remoto existe, se obtiene su checksum SHA256 via `exec_command` con `sha256sum` | High |
| R3 | Si los checksums coinciden, no se sube y se loggea `SKIP <remote_path> (unchanged)` | High |
| R4 | Si el fichero remoto no existe o los checksums difieren, se sube normalmente | High |
| R5 | `--force-upload` flag omite la verificación de checksum y sube siempre | High |
| R6 | `DryRunRunner` muestra `[DRY RUN] SKIP` o `[DRY RUN] UPLOAD` según el resultado de la verificación | Medium |
| R7 | El comportamiento con `--dry-run` debe predecir el skip sin ejecutar comandos remotos | Medium |

## Non-functional requirements

| ID | Requirement |
|----|-------------|
| NF1 | Los tests mockean `IConnection.exec_command` y `paramiko.SFTPClient`; sin conexiones reales |
| NF2 | SHA256 se calcula localmente con `hashlib.sha256()` de la stdlib (sin nueva dependencia) |
| NF3 | El mensaje SKIP se muestra en consola como `[host] SKIP   script.sh (unchanged)` |

## Out of scope

- Algoritmo configurable (solo SHA256, no MD5)
- Verificación recursiva de directorios completos
- Caché persistente de checksums entre ejecuciones
