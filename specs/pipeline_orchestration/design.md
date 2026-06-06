# Technical Design — pipeline_orchestration

## Overview

Añadir un motor de orquestación DAG sobre el sistema de kits existente. El fichero de pipeline YAML define steps con dependencias opcionales. El motor resuelve el grafo, ejecuta en paralelo los steps independientes, interpola outputs entre steps y gestiona fallos con propagación de skip.

## Nuevos módulos

### ikctl/orchestration/parser.py — PipelineParser

Responsabilidad: leer y validar el fichero YAML de pipeline.

```python
@dataclass(frozen=True)
class StepDef:
    id: str
    kit: str
    servers: str
    sudo: bool = False
    params: list[str] = field(default_factory=list)
    needs: list[str] = field(default_factory=list)

@dataclass(frozen=True)
class PipelineDef:
    name: str
    steps: list[StepDef]

class PipelineParser:
    def parse(self, path: str) -> PipelineDef:
        """Lee el YAML y devuelve PipelineDef. Lanza ConfigError si inválido."""
```

### ikctl/orchestration/dag.py — DAGResolver

Responsabilidad: resolver el grafo de dependencias y detectar ciclos.

```python
class DAGResolver:
    def resolve(self, steps: list[StepDef]) -> list[list[StepDef]]:
        """
        Devuelve lista de 'waves' (grupos de steps que pueden ejecutarse en paralelo).
        Wave 0: steps sin needs.
        Wave 1: steps cuyos needs están todos en wave 0.
        ...
        Lanza ConfigError si hay ciclos.
        """
```

Algoritmo: Kahn's algorithm (topological sort por capas).

### ikctl/orchestration/interpolator.py — OutputInterpolator

Responsabilidad: parsear KEY=VALUE del stdout y resolver `{{ steps.<id>.<KEY> }}`.

```python
class OutputInterpolator:
    def extract(self, stdout: str) -> dict[str, str]:
        """Extrae pares KEY=VALUE de stdout. Ignora líneas que no siguen el patrón."""

    def interpolate(self, template: str, outputs: dict[str, dict[str, str]]) -> str:
        """
        Resuelve {{ steps.<id>.<KEY> }} usando el dict acumulado de outputs.
        Lanza ConfigError si el step o la variable no existen.
        """
```

### ikctl/orchestration/runner.py — OrchestrationRunner

Responsabilidad: ejecutar el DAG completo.

```python
@dataclass
class StepResult:
    id: str
    status: str   # "ok" | "failed" | "skipped"
    outputs: dict[str, str]
    stdout: str
    stderr: str

class OrchestrationRunner:
    def run(self, pipeline: PipelineDef, options) -> list[StepResult]:
        """
        1. Resuelve el DAG en waves
        2. Por cada wave: ejecuta los steps en paralelo (ThreadPoolExecutor)
        3. Acumula outputs de cada step
        4. Interpola params de steps posteriores
        5. Si un step falla, marca sus dependientes como skipped
        6. Devuelve list[StepResult]
        """
```

## Flujo de datos

```
ikctl --pipeline deploy.yaml
    → main.py
        → PipelineParser.parse(path) → PipelineDef
        → DAGResolver.resolve(steps) → list[list[StepDef]]  (waves)
        → OrchestrationRunner.run(pipeline, options)
            → Wave 0: ThreadPoolExecutor → [StepResult, ...]
            → OutputInterpolator.extract(stdout) → dict outputs
            → Wave 1: interpola params → ThreadPoolExecutor → [StepResult, ...]
            → ...
        → imprimir resumen (Rich table)
```

## Integración con el sistema existente

`OrchestrationRunner` reutiliza `RemoteRunner` / `LocalRunner` para ejecutar cada step. Por cada step:

```python
# Resolución de servidor y kit igual que --install
kit = KitRepository(config).resolve(step.kit)
servers = ServerRepository(config).resolve(step.servers)
runner = RemoteRunner(connection_factory, ...)
results = runner.run(kit, servers, options_with_step_params)
# Extraer outputs del stdout de cada RunResult
```

## Manejo de fallos

```
Wave 0: [A, B] → A=OK, B=FAILED
Wave 1: [C needs A, D needs B] → C ejecuta, D=SKIPPED
Wave 2: [E needs C, D] → E ejecuta si C=OK, si no SKIPPED
```

Un step es SKIPPED si cualquiera de sus `needs` no es `ok`.

## Salida con Rich

```
Pipeline: install-kubernetes-cluster

  Wave 1  ──────────────────────────────
  ✓ packages    all-nodes    0:12
  
  Wave 2  ──────────────────────────────
  ✓ docker      all-nodes    0:45
  
  Wave 3  ──────────────────────────────
  ✓ init-master master       1:03
  
  Wave 4  ──────────────────────────────
  ✓ join-workers workers     0:28

┌─────────────────────────────────────┐
│ 4 steps OK · 0 FAILED · 0 SKIPPED  │
└─────────────────────────────────────┘
```

## Decisions & trade-offs

| Decision | Alternatives | Reason |
|----------|-------------|--------|
| Waves (Kahn) en lugar de ejecución step-a-step | Ejecutar uno a uno | Maximiza paralelismo natural del DAG |
| KEY=VALUE en stdout | Ficheros temporales, env vars | Más simple, sin efectos secundarios en el servidor |
| `{{ steps.id.KEY }}` como sintaxis | Jinja2, f-strings | Sin dependencias externas; regex simple |
| Reusar RemoteRunner/LocalRunner | Nueva capa de ejecución | Reutiliza toda la lógica existente (SFTP, SSH, timeouts) |

## Risks

- Si un kit escribe muchas líneas KEY=VALUE no intencionadas, se capturan igualmente. Documentar que el formato es intencional.
- La interpolación se hace antes de ejecutar el step — si el output del step anterior está vacío, falla con error claro.
