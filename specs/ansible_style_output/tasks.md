# Tasks — ansible_style_output

## T1 — Añadir `debug` a `RunOptions` (si no existe)

- Fichero: `ikctl/runner/base.py`
- Añadir `debug: bool = False` al dataclass `RunOptions`
- Añadir `debug=getattr(args, "debug", False)` en el bloque `run_options = RunOptions(...)` de `ikctl/main.py`

## T2 — Eliminar Rich Progress del runner remoto

- Fichero: `ikctl/runner/remote.py`
- Eliminar imports: `BarColumn`, `Progress`, `TextColumn`, `TimeElapsedColumn`
- Eliminar el bloque `with Progress(...) as progress:` y todo su contenido
- Reemplazar por bucle simple con `_console.print(f"[{label}] UPLOAD  {fname:<40} {status}")`

## T3 — Reemplazar logging de RUN por línea de consola

- Fichero: `ikctl/runner/remote.py`
- Después de `executor.execute(full_cmd)`, imprimir `[{label}] RUN     {script:<40} OK/FAILED`
- Solo imprimir stdout/stderr del host si `options.debug` es True

## T4 — Tests nuevos en `test_remote_runner.py`

- `test_upload_prints_ok_line`: mock sftp, verificar que la salida contiene `UPLOAD` y `OK`
- `test_run_prints_ok_line`: mock executor, verificar que contiene `RUN` y `OK`
- `test_run_prints_failed_line`: exit_code != 0, verificar `FAILED`
- `test_no_stdout_without_debug`: `RunOptions(debug=False)`, stdout del host no aparece
- `test_stdout_with_debug`: `RunOptions(debug=True)`, stdout del host sí aparece

## T5 — Verificar tests existentes en verde

- Ejecutar `uv run pytest tests -q` y confirmar 0 failures
