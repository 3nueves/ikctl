# Review — feature 8 (parallel_hosts)

**Veredicto:** APPROVED

## Checkpoints

- C1: [x] `./init.sh` termina con `[OK] Entorno listo`
- C2: [x] 102 tests pasan (13 nuevos en `tests/test_parallel_hosts.py`, 89 anteriores — todos verdes, 0 skips)
- C3: [x] Nombres siguen convenciones: `_run_on_host`, `_max_workers`, `max_workers`, `parallel_workers`, `RemoteRunner` — todos correctos
- C4: [x] `self._logger = logging.getLogger(__name__)` en `RemoteRunner.__init__`; no hay `print()` en capas internas
- C5: [x] Excepciones capturadas en `Pipeline._run()` y `main.py`; `sys.exit(1)` solo en `pipeline.py` al final de `_print_results()`
- C6: [x] `tests/test_parallel_hosts.py` usa `MagicMock` para conexiones; no hay SSH real
- C7: [x] `_run_on_host` tiene tests de camino feliz (prefijo, close en éxito) y de error (host que falla, close en excepción)
- C8: [x] Tests son funciones `def test_*`; fixtures `@pytest.fixture` para `kit`, `single_server`, `two_servers`, `three_servers`; sin herencia de `unittest.TestCase`
- C9: [x] `RemoteRunner` permanece en `ikctl/runner/remote.py`; `pipeline.py` imprime el resumen; `main.py` solo parsea y construye — capas respetadas
- C10: [x] `concurrent.futures` es stdlib; no se añaden dependencias externas
- C11: [x] Todos los criterios de `acceptance` verificados:
  - `ThreadPoolExecutor` usado en `run()` (línea 40-44 de `remote.py`)
  - `--parallel-workers N` presente en `main.py` (línea 98-104)
  - Prefijo `[{host}]` en `all_stdout.append(f"[{host}] {upload_line}")` y `all_stdout.append(f"[{host}] {line}")` (líneas 81, 87)
  - Resumen `N hosts OK, M hosts FAILED` en `pipeline.py` línea 91
  - Host que falla: excepción capturada con `except (OSError, RuntimeError)`, devuelve `RunResult(success=False)`; los demás continúan via `ThreadPoolExecutor.map()`
  - Exit code 1 si algún host falla: `sys.exit(1)` en `pipeline.py` línea 94
  - `tests/test_parallel_hosts.py` cubre N conexiones, `close()` siempre llamado, fallo aislado, prefijo `[host]`, límite de workers via mock de `ThreadPoolExecutor`

## Verificaciones específicas del diseño (specs/parallel_hosts/design.md)

- `RemoteRunner.__init__` acepta `max_workers: int = 4`: [x] línea 23 de `remote.py`
- `run()` usa `ThreadPoolExecutor.map()` en lugar de bucle for: [x] líneas 40-44 de `remote.py`
- `_run_on_host(host, kit, options) -> RunResult` con `try/finally` para `conn.close()`: [x] líneas 48-110 de `remote.py`
- `stdout` de cada `RunResult` tiene líneas prefijadas con `[{host}]`: [x] líneas 81 y 87 de `remote.py`
- Si un host lanza excepción devuelve `RunResult(success=False)` y los demás continúan: [x] líneas 101-108 de `remote.py`
- `main.py` acepta `--parallel-workers N` (int, default 4): [x] líneas 98-104 de `main.py`
- `main.py` pasa `max_workers` a `RemoteRunner`: [x] línea 52 de `main.py`
- `Pipeline` imprime resumen `N hosts OK, M hosts FAILED`: [x] línea 91 de `pipeline.py`
- Exit code 1 si algún host falla: [x] línea 94 de `pipeline.py`
- No hay estado mutable compartido entre threads: [x] cada thread crea su propio `conn`, `sftp`, `executor`, `all_stdout`, `all_stderr` dentro de `_run_on_host`

## Observaciones

Sin cambios requeridos. La implementación sigue fielmente el diseño del spec. El test `test_parallel_workers_limits_concurrent_threads` valida via mock de `ThreadPoolExecutor` que se instancia con `max_workers=2`, lo cual es correcto dado que probar límite de concurrencia real requeriría sleeps. La captura de `(OSError, RuntimeError)` es exactamente la acordada en el spec (tabla "Decisions & trade-offs").
