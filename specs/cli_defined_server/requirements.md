# Requirements — cli_defined_server

## Functional requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| R1 | El usuario puede pasar `--host <IP>` para definir un servidor destino sin archivo YAML | High |
| R2 | El flag `--host` es repetible: `--host 10.0.0.1 --host 10.0.0.2` ejecuta en paralelo en ambos | High |
| R3 | El usuario puede especificar `--user <name>` para el usuario SSH (default: `root`) | High |
| R4 | El usuario puede especificar `--password <pass>` para autenticación SSH por contraseña | High |
| R5 | El usuario puede especificar `--port <n>` para el puerto SSH (default: `22`) | High |
| R6 | El usuario puede especificar `--key <path>` para autenticación SSH por clave privada | High |
| R7 | Cuando `--host` está presente, NO se carga `servers/config.yaml` — la conexión se construye solo con valores CLI | High |
| R8 | Cuando `--host` NO está presente, el comportamiento es idéntico al actual | High |
| R9 | `--host` es compatible con `--install`, `--pipeline`, `--dry-run` y el resto de flags existentes | High |
| R10 | `sudo_password` con `--host` se resuelve: `--sudo-password` > `--password` > `None` | High |

## Non-functional requirements

| ID | Requirement |
|----|-------------|
| NF1 | Sin `--host`, `sudo_password` se resuelve igual que antes: `--sudo-password` > `.secrets` > `servers.password` > `None` |
| NF2 | Los secrets y config_mode no se cargan del YAML cuando `--host` está presente |
| NF3 | Los timeouts usan defaults (30.0 connect, 120.0 exec) cuando se usa `--host` sin `--timeout-connect`/`--timeout-exec` |