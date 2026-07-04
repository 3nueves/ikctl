# Requirements — parallel_hosts

## Functional requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| R1 | Cuando un `ServerGroup` tiene múltiples hosts, ejecutar el kit en todos concurrentemente | High |
| R2 | `--parallel-workers N` controla el máximo de threads simultáneos (default 4) | High |
| R3 | Cada línea de output debe estar prefijada con el host: `[192.168.1.10] UPLOAD: ...` | High |
| R4 | Al finalizar, imprimir un resumen: `N hosts OK, M hosts FAILED` | High |
| R5 | Si un host falla, los demás hosts continúan su ejecución (no se aborta el grupo) | High |
| R6 | El exit code final es 0 solo si todos los hosts terminaron con `success=True` | High |
| R7 | Con un solo host, el comportamiento es idéntico al actual (sin regresión) | Medium |

## Non-functional requirements

| ID | Requirement |
|----|-------------|
| NF1 | Los tests mockean `IConnection` por host; sin conexiones SSH reales |
| NF2 | El diseño no introduce estado compartido mutable entre threads |
| NF3 | El número de threads activos simultáneos no supera `max_workers` |

## Out of scope

- Cancelación de hosts en vuelo si otro falla (R5 lo prohíbe explícitamente)
- Orden garantizado de los resultados (el orden puede variar según velocidad de cada host)
- Barra de progreso en tiempo real por host
