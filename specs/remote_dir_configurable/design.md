# Technical Design — remote_dir_configurable

## Overview

Añadir `remote_dir` configurable a nivel de kit (en `ikctl.yaml`) y a nivel de CLI
(`--remote-dir`). La precedencia es: CLI > ikctl.yaml > default `.ikctl/<kit.name>/`.

La resolución se hace en `RemoteRunner` y `DryRunRunner` justo antes de usarlo,
no en `KitRepository` (el repo no debe saber de opciones de ejecución).

## Classes / Interfaces affected

### KitPipeline (`ikctl/config/models.py`)

- **Nuevo campo:** `remote_dir: str | None = None`

```python
@dataclass(frozen=True)
class KitPipeline:
    uploads: list[str]
    pipeline: list[str]
    outputs: dict[str, str] = field(default_factory=dict)
    name: str = ""
    remote_dir: str | None = None
```

### KitRepository.resolve() (`ikctl/config/kit_repo.py`)

- **Cambio:** Leer `kits.remote_dir` del YAML si existe

```python
remote_dir: str | None = kit_config["kits"].get("remote_dir", None)
return KitPipeline(uploads=uploads, pipeline=pipeline, outputs=outputs, name=name, remote_dir=remote_dir)
```

### RunOptions (`ikctl/runner/base.py`)

- **Nuevo campo:** `remote_dir: str | None = None`

### main.py

- **Nuevo flag:** `--remote-dir` (`type=str`, `default=None`)
- Pasar a `RunOptions(remote_dir=args.remote_dir, ...)`

### RemoteRunner._run_on_host() (`ikctl/runner/remote.py`)

- **Cambio:** Resolver `remote_dir` al inicio del método y usarlo donde hoy está
  `f".ikctl/{kit.name}"`. La función auxiliar se puede definir inline o como
  helper privado del módulo.

```python
def _resolve_remote_dir(kit: KitPipeline, options: RunOptions) -> str:
    """Resolve remote upload directory with precedence: CLI > ikctl.yaml > default."""
    if options.remote_dir:
        return options.remote_dir
    if kit.remote_dir:
        return kit.remote_dir
    return f".ikctl/{kit.name}"

# Uso:
remote_dir = _resolve_remote_dir(kit, options)
remote_path = f"{remote_dir}/{os.path.basename(local_path)}"
```

- El `remote_dir` se usa también para el `cd` en la ejecución de pasos del pipeline

### DryRunRunner.run() (`ikctl/runner/dry_run.py`)

- **Cambio:** Usar `_resolve_remote_dir()` para construir la ruta remota
- Se puede importar la función desde `remote.py` o duplicarla; por simplicidad
  se extrae a un helper compartido.

### DryRunRunner.run() (`ikctl/runner/dry_run.py`)

- Antes usaba `f".ikctl/{Path(upload).parent.name}/{Path(upload).name}"`, ahora usa
  el `remote_dir` resuelto.

### Helper compartido

Para no duplicar lógica, se extrae `_resolve_remote_dir` a un módulo compartido,
por ejemplo `ikctl/runner/utils.py`, importable desde `remote.py` y `dry_run.py`.

```python
"""Shared runner utilities."""
from __future__ import annotations

from ikctl.config.models import KitPipeline
from ikctl.runner.base import RunOptions


def resolve_remote_dir(kit: KitPipeline, options: RunOptions) -> str:
    """Resolve remote upload directory: CLI > ikctl.yaml > .ikctl/<kit.name>/."""
    if options.remote_dir:
        return options.remote_dir
    if kit.remote_dir:
        return kit.remote_dir
    return f".ikctl/{kit.name}"
```

## Data flow

```
ikctl.yaml (kits.remote_dir)
    → KitRepository.resolve()
        → KitPipeline(remote_dir=...)

--remote-dir CLI flag
    → main.py
        → RunOptions(remote_dir=...)

RemoteRunner._run_on_host()
    → resolve_remote_dir(kit, options)
        → options.remote_dir? (CLI)
        → kit.remote_dir? (YAML)
        → ".ikctl/<kit.name>/" (default)
```

## Decisions & trade-offs

| Decision | Alternatives considered | Reason |
|----------|------------------------|--------|
| Helper compartido en `ikctl/runner/utils.py` | Importar desde `remote.py` | Evita import circular; ambos runners lo necesitan |
| Resolución en runner, no en repo | Resolver en KitRepository | KitRepository no debe depender de opciones de ejecución; SRP |
| `remote_dir` en `KitPipeline` | Solo en `RunOptions` | El valor del YAML es del kit, no de la ejecución; el CLI override va en options |

## Risks

- Si `remote_dir` empieza con `/` (ruta absoluta), la creación de directorio remoto
  podría fallar o comportarse inesperadamente. No se valida — queda como
  responsabilidad del autor del kit.
- `DryRunRunner` cambia su output actual (usaba `Path(upload).parent.name` en
  lugar de `kit.name`). Este cambio alinea dry-run con el comportamiento real.
