# Implementer report — feature 27: ansible_style_output

## Ficheros modificados

| Fichero | Cambio |
|---------|--------|
| `ikctl/runner/base.py` | Añadido `debug: bool = False` al dataclass `RunOptions` |
| `ikctl/main.py` | Añadido `debug=getattr(args, "debug", False)` al constructor de `RunOptions` |
| `ikctl/runner/remote.py` | Eliminado import `BarColumn, Progress, TextColumn, TimeElapsedColumn`; reemplazado bloque `with Progress(...)` por bucle simple con `_console.print`; reemplazado logging de RUN por línea de consola con soporte `options.debug` |
| `tests/test_remote_runner.py` | Añadidos 5 tests nuevos; añadida función auxiliar `_make_test_console()` |
| `tests/test_output_mode.py` | Reemplazado `test_run_on_host_uses_progress_for_uploads` por `test_run_on_host_upload_prints_ok_line` |

## Tests añadidos / modificados

- **Añadidos (5)** en `tests/test_remote_runner.py`:
  - `test_upload_prints_ok_line`
  - `test_run_prints_ok_line`
  - `test_run_prints_failed_line`
  - `test_no_stdout_without_debug`
  - `test_stdout_with_debug`

- **Reemplazado (1)** en `tests/test_output_mode.py`:
  - `test_run_on_host_uses_progress_for_uploads` → `test_run_on_host_upload_prints_ok_line`

## Resultado de `uv run pytest tests -v`

```
270 passed, 1 warning in 0.86s
```

(265 tests previos + 5 nuevos = 270 total; el test reemplazado mantiene el recuento)

## Decisiones de diseño

1. **`label = host`**: Según el diseño, el label es simplemente el host (IP o hostname). `ServerGroup` no tiene nombres individuales por host; añadirlos es feature futura (RF-4 satisfecho parcialmente).

2. **`options.debug` en `_build_remote_command`**: No hay cambios aquí; `debug` solo controla si se imprime el stdout/stderr del host en la consola, no la construcción del comando.

3. **`all_stdout` conservado para UPLOAD**: Se sigue llenando `all_stdout` con la línea de upload para que `RunResult.stdout` tenga trazabilidad, aunque la salida principal ahora va a `_console`.

4. **Test `test_run_on_host_uses_progress_for_uploads` eliminado**: No tiene sentido mantenerlo porque `Progress` ya no se usa. Se reemplaza por `test_run_on_host_upload_prints_ok_line` que verifica el nuevo formato de línea.

5. **`_make_test_console()`**: Función auxiliar que crea un `Console` con `no_color=True` escribiendo a `StringIO`, para capturar la salida de `_console` en tests sin efectos de color ANSI.
