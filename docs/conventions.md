# Convenciones de código — ikctl

> Homogeneidad extrema. El código nuevo debe parecer que siempre estuvo aquí.

## Entorno

- **Python:** 3.13+ (declarado en `pyproject.toml` como `requires-python = ">=3.13"`).
- **Gestor de paquetes:** uv. Comandos: `uv add`, `uv run`, `uv sync`.
- **Dependencias de producción:** `paramiko>=3.0`, `pyaml`, `envyaml`.
- **Dependencias de dev** (en `[dependency-groups].dev`): `pytest>=8.0`, `ruff>=0.5`.
- **Formato y linting:** ruff. Configurado en `pyproject.toml` bajo `[tool.ruff]`.
- **Líneas:** máximo 100 caracteres.

## Nombres

| Tipo | Convención | Ejemplo |
|------|-----------|---------|
| Módulos | `snake_case` | `server_repo.py` |
| Clases concretas | `PascalCase` | `ServerRepository` |
| ABCs / interfaces | `I` + PascalCase | `IConnection`, `IRunner` |
| Funciones / métodos | `snake_case` | `resolve()` |
| Variables | `snake_case` | `server_group` |
| Constantes de módulo | `UPPER_SNAKE` | `DEFAULT_TIMEOUT` |
| Métodos privados | prefijo `_` | `_load_raw_config()` |
| Campos de @dataclass | `snake_case` | `key_filename` |

## Type hints — Python 3.13

Usar **siempre** la sintaxis moderna. No importar `Optional`, `List`, `Dict`, `Union` de `typing`.

```python
# Correcto
def resolve(self, group: str | None = None) -> ServerGroup: ...
pkey: str | list[str] | None = None

# Incorrecto
from typing import Optional, List
def resolve(self, group: Optional[str] = None) -> ServerGroup: ...
```

Type aliases con la sintaxis PEP 695:

```python
type CommandResult = tuple[str, str, int]
type HostList = list[str]
```

## Dataclasses

Usar `@dataclass` para modelos de datos y objetos de valor.
`frozen=True` cuando el objeto no debe mutarse tras creación.

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class ServerGroup:
    user: str
    port: int
    hosts: list[str]
    password: str = "no_pass"
    pkey: str | None = None
```

## ABCs (interfaces)

```python
from abc import ABC, abstractmethod

class IConnection(ABC):
    """Contract for SSH-like connections."""

    @abstractmethod
    def exec_command(self, command: str) -> tuple[str, str, int]:
        """Returns (stdout, stderr, exit_code)."""

    @abstractmethod
    def close(self) -> None: ...
```

## Estructura de clase

```python
"""Module description — one line."""
from __future__ import annotations

import logging

class KitRepository:
    """Resolves kit configurations from the loaded config."""

    def __init__(self, config: IkctlConfig) -> None:
        self._config = config
        self._logger = logging.getLogger(__name__)
```

Usar `logging.getLogger(__name__)`, no el patrón antiguo `__name__.split(".")[-1]`.

## Imports

Orden: stdlib → terceros → locales. Una línea por módulo.

```python
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

import paramiko

from ikctl.config.models import ServerGroup
```

## Strings

- Comillas dobles `"..."` siempre.
- f-strings para interpolación. No `.format()` ni `%`.

## Manejo de errores

Las capas internas **lanzan excepciones del dominio**. Solo `Pipeline` y `main.py`
llaman a `sys.exit()`. Excepciones en `ikctl/config/exceptions.py`:

```python
class IkctlError(Exception):
    """Base para todos los errores de ikctl."""

class ConfigError(IkctlError): ...
class KitNotFoundError(IkctlError): ...
class ServerNotFoundError(IkctlError): ...
```

Captura específica, nunca `except Exception` a secas salvo en el nivel más alto.

```python
# Correcto — capa interna
def resolve(self, name: str) -> KitPipeline:
    if name not in self._kits:
        raise KitNotFoundError(f"Kit '{name}' not found")
    return self._kits[name]

# Correcto — Pipeline
try:
    kit = kit_repo.resolve(options.install)
except KitNotFoundError as e:
    print(f"\nError: {e}\n", file=sys.stderr)
    sys.exit(1)
```

## Archivos: siempre context managers

```python
# Correcto
with open(path, encoding="utf-8") as f:
    data = f.read()

# Incorrecto
f = open(path)
data = f.read()
f.close()
```

## Logging vs print

- `self._logger.info/warning/error(...)` en capas internas (config, connection, runner, executor).
- `print()` solo en `pipeline.py`, `view.py`, `logs.py`.

## Colores ANSI (solo en logs.py)

```python
GREEN = "\033[1;32m"
RED   = "\x1b[31;1m"
RESET = "\x1b[0m"
```

## Censurar secretos

```python
import re

def _censor(command: str) -> str:
    return re.sub(r"echo\s+\S+\s*\|", "echo *** |", command)
```

Aplicar antes de cualquier `logger.info()` o salida que incluya el comando ejecutado.

## Tests

- Un archivo por módulo: `tests/test_<módulo>.py`.
- Funciones `def test_*` o clases `class Test*` sin herencia.
- Fixtures de pytest (`@pytest.fixture`) para estado compartido.
- Mocks con `unittest.mock.patch` sobre `paramiko.SSHClient`. Nunca SSH real.
- Nombres descriptivos: `test_resolve_raises_kit_not_found_when_name_missing`.
- Runner: `uv run pytest tests -v`.

## Docstrings

Una línea por módulo y por método público.

```python
"""Resolves kit configurations from the loaded ikctl config."""

def resolve(self, name: str) -> KitPipeline:
    """Returns the KitPipeline for the given kit name."""
```
