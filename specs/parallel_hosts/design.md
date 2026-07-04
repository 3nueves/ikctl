# Technical Design — parallel_hosts

## Overview

Sustituir el bucle secuencial `for host in servers.hosts` en `RemoteRunner.run()` por
`ThreadPoolExecutor.map()`. Cada thread gestiona un host de forma completamente independiente
(crea su propia conexión, sube archivos, ejecuta pipeline y cierra). No hay estado compartido
mutable entre threads.

## Classes / Interfaces affected

### RemoteRunner (`ikctl/runner/remote.py`)

- **Cambio:** Constructor añade `max_workers: int = 4`
- **Cambio:** `run()` usa `ThreadPoolExecutor(max_workers=self._max_workers)` en lugar del bucle for
- **Sin cambio:** la signatura de `IRunner.run()` no cambia

```python
class RemoteRunner(IRunner):
    def __init__(
        self,
        connection_factory: Callable[[str], IConnection],
        max_workers: int = 4,
    ) -> None:
        self._connection_factory = connection_factory
        self._max_workers = max_workers
        self._logger = logging.getLogger(__name__)

    def run(self, kit: KitPipeline, servers: ServerGroup, options) -> list[RunResult]:
        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            results = list(pool.map(
                lambda host: self._run_on_host(host, kit, options),
                servers.hosts,
            ))
        return results

    def _run_on_host(self, host: str, kit: KitPipeline, options) -> RunResult:
        conn = self._connection_factory(host)
        try:
            # upload + execute — igual que antes pero prefijando output con [host]
            ...
            return RunResult(host=host, success=True, stdout=prefixed_stdout, stderr="")
        except (OSError, RuntimeError) as exc:
            return RunResult(host=host, success=False, stdout="", stderr=str(exc))
        finally:
            conn.close()
```

### main.py

- Añadir `--parallel-workers N` (default 4)
- Pasar `max_workers` a `RemoteRunner(connection_factory, max_workers=args.parallel_workers)`

### Pipeline (`ikctl/pipeline.py`)

- `_print_results()` (o equivalente) imprime el prefijo `[host]` y el resumen final
- Exit code 0 solo si `all(r.success for r in results)`

## Output format

Cada línea de stdout de un host va prefijada en `RunResult.stdout`:
```
[192.168.1.10] UPLOAD: /path/to/script.sh → .ikctl/docker/script.sh
[192.168.1.10] EXEC: bash script.sh
[10.0.0.5]     UPLOAD: /path/to/script.sh → .ikctl/docker/script.sh
[10.0.0.5]     EXEC: bash script.sh
```

Resumen final (impreso por Pipeline):
```
2 hosts OK, 0 hosts FAILED
```

## Decisions & trade-offs

| Decision | Alternatives considered | Reason |
|----------|------------------------|--------|
| `ThreadPoolExecutor` | `asyncio` | Paramiko no es async-native; threads son más simples |
| `pool.map()` | `pool.submit()` + `as_completed()` | `map()` mantiene orden; más simple para agregar resultados |
| Capturar `(OSError, RuntimeError)` por host | Dejar que propague | R5: si un host falla, los demás continúan |
| Prefijo `[host]` en `RunResult.stdout` | Prefijo en tiempo real | No hay estado compartido en threads; más seguro |

## Risks

- `pool.map()` no garantiza orden de ejecución, pero sí orden de resultados (igual al orden de `servers.hosts`)
- Si `_connection_factory` lanza una excepción no capturada, `pool.map()` la re-lanzará; hay que asegurar que `_run_on_host` captura todo
