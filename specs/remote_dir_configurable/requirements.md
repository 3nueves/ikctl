# Requirements — remote_dir_configurable

## Functional requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| R1 | `KitPipeline` tiene campo `remote_dir: str \| None = None` | High |
| R2 | `kit_repo.py` lee `kits.remote_dir` del `ikctl.yaml` si existe | High |
| R3 | `RunOptions` tiene campo `remote_dir: str \| None = None` | High |
| R4 | `main.py` acepta `--remote-dir STRING` (default None) | High |
| R5 | `RemoteRunner` resuelve remote_dir con precedencia: CLI > ikctl.yaml > `.ikctl/<kit.name>/` | High |
| R6 | `DryRunRunner` usa el mismo remote_dir resuelto | Medium |
| R7 | Si no se especifica remote_dir ni en ikctl.yaml ni CLI, el comportamiento es idéntico al actual | High |

## Non-functional requirements

| ID | Requirement |
|----|-------------|
| NF1 | Tests con mocks, sin conexiones reales |
| NF2 | Sin nuevas dependencias externas |
| NF3 | `KitPipeline` sigue siendo `frozen=True` |

## Out of scope

- `remote_dir` no soporta expansión de variables (ej: `{{ kit.name }}`)
- No se valida que `remote_dir` exista en remoto; se crea igual que hoy
