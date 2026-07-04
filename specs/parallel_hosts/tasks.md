# Implementation tasks — parallel_hosts

> Ordered list. Complete each task before starting the next.
> Update [ ] to [x] as you go. Document blockers in progress/current.md.

- [x] T1: Añadir `max_workers: int = 4` al constructor de `RemoteRunner` en `ikctl/runner/remote.py`
- [x] T2: Extraer la lógica de un host a `_run_on_host(host, kit, options) -> RunResult`; asegurar `try/finally` con `conn.close()`
- [x] T3: Sustituir el bucle `for host in servers.hosts` por `ThreadPoolExecutor.map()` en `RemoteRunner.run()`
- [x] T4: Prefijar cada línea de `RunResult.stdout` con `[{host}]`
- [x] T5: Añadir `--parallel-workers N` (int, default 4) a `main.py`
- [x] T6: Pasar `max_workers=args.parallel_workers` a `RemoteRunner(...)` en `main.py`
- [x] T7: En `Pipeline`, imprimir resumen final `N hosts OK, M hosts FAILED` tras `run()`
- [x] T8: Exit code 0 solo si `all(r.success for r in results)`; `sys.exit(1)` si alguno falló
- [x] T9: Crear `tests/test_parallel_hosts.py`:
  - Mock de `IConnection` por host
  - Verificar que se crean N conexiones para N hosts
  - Verificar que `connection.close()` se llama por cada host (incluso si falla)
  - Verificar que si un host falla, los demás devuelven `success=True`
  - Verificar que el output de cada host lleva prefijo `[host]`
  - Verificar que `--parallel-workers 2` limita los threads activos a 2
- [x] T10: Ejecutar `./init.sh` — debe terminar con `[OK] Entorno listo`
