# Technical Design — init_command

## Overview

Añadir `ikctl --init` como comando de onboarding independiente. Crea una estructura de configuración funcional paso a paso, con modo interactivo (por defecto) y modo automático (`--auto`). No depende de que exista configuración previa.

## Nuevo módulo

### `ikctl/init/wizard.py` — InitWizard

Responsabilidad única: orquestar la creación de los 4 artefactos de configuración.

```python
@dataclass
class InitPaths:
    config_file: Path       # ~/.ikctl/config
    servers_file: Path      # ~/.ikctl/servers/config.yaml
    kit_dir: Path           # ~/kits/show-date/
    pipelines_dir: Path     # ~/.ikctl/pipelines/

class InitWizard:
    def __init__(self, base: Path | None = None, auto: bool = False, force: bool = False) -> None:
        """
        base: directorio raíz para tests (default: Path.home()).
        auto: si True, no pregunta confirmación en cada paso.
        force: si True, sobrescribe archivos existentes.
        """

    def run(self) -> list[Path]:
        """Ejecuta los 4 pasos. Devuelve lista de paths creados."""

    def _step(self, n: int, title: str, description: str, create_fn: Callable) -> Path | None:
        """
        Muestra el número de paso, título y descripción.
        En modo interactivo pregunta confirmación.
        Llama a create_fn() si el archivo no existe (o --force).
        Devuelve el path creado o None si se omitió.
        """
```

Cada `_step` imprime con Rich el número de paso, el propósito del archivo y la ruta. En modo `--auto` no pregunta; en modo interactivo muestra `[Enter para continuar / s para omitir]`.

### `ikctl/init/__init__.py`

Vacío, marca el paquete.

## Integración con `main.py`

```python
# main.py — tras parse_args()
if args.init:
    from ikctl.init.wizard import InitWizard
    wizard = InitWizard(auto=args.auto, force=args.force)
    wizard.run()
    sys.exit(0)
```

Nuevos argumentos en el parser:
- `--init` (flag booleano)
- `--auto` (flag booleano, solo relevante con `--init`)
- `--force` (flag booleano, solo relevante con `--init`)

`--init` se añade al check de argumentos accionables (feature 22) para que `ikctl --init` no muestre el help.

## Lógica de idempotencia

```python
def _write_if_absent(path: Path, content: str, force: bool) -> bool:
    """Escribe content en path solo si no existe o force=True. Devuelve True si escribió."""
    if path.exists() and not force:
        console.print(f"  [yellow]skip[/yellow] {path} (ya existe, usa --force para sobrescribir)")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return True
```

## Panel de resumen final (Rich)

```
┌─────────────────────────────────────────────────────┐
│  ikctl init completado                              │
│                                                     │
│  Archivos creados:                                  │
│    ✓ ~/.ikctl/config                                │
│    ✓ ~/.ikctl/servers/config.yaml                   │
│    ✓ ~/kits/show-date/ikctl.yaml                    │
│    ✓ ~/kits/show-date/date.sh                       │
│    ✓ ~/.ikctl/pipelines/example.yaml                │
│                                                     │
│  Prueba tu instalación:                             │
│    ikctl --list kits                                │
│    ikctl --install show-date                        │
│    ikctl --pipeline example                         │
└─────────────────────────────────────────────────────┘
```

## Flujo de datos

```
ikctl --init [--auto] [--force]
    → main.py detecta args.init
    → InitWizard(auto, force).run()
        → _step(1, "Configuración principal", ..., _create_config)
        → _step(2, "Servidores", ..., _create_servers)
        → _step(3, "Kit de ejemplo", ..., _create_kit)
        → _step(4, "Pipeline de ejemplo", ..., _create_pipeline)
        → _print_summary(created_paths)
    → sys.exit(0)
```

## Decisions & trade-offs

| Decision | Alternatives | Reason |
|----------|-------------|--------|
| Módulo `ikctl/init/` separado | Añadir todo a `main.py` | SRP: main.py ya orquesta, no debe contener lógica de creación de archivos |
| `base` param en `InitWizard` | Parchear `Path.home()` en tests | Más limpio: tests pasan `tmp_path`, producción usa default `Path.home()` |
| 4 pasos fijos | Config dinámica | El wizard es onboarding, no un configurador completo |
| `--auto` flag separado | `--init` siempre auto | Permite elegir entre experiencia guiada y scripting |

## Risks

- El usuario puede tener `~/.ikctl/config` ya configurado con un contexto distinto a `demo`. La idempotencia protege: sin `--force`, se omiten los archivos existentes.
- `mode: local` en el demo puede confundir si el usuario quiere SSH. El wizard lo explica explícitamente en el paso 1.
