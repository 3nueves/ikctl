# Implementer session — feature 27 bug fixes (27b)

## 1. Ficheros modificados

- `ikctl/runner/remote.py`
- `ikctl/pipeline.py`

## 2. Líneas exactas cambiadas

### ikctl/runner/remote.py — Bug 1 (línea 108 eliminada)

Eliminada la línea que acumulaba el formato legacy en `all_stdout`:

```python
# ELIMINADO:
all_stdout.append(f"[{label}] UPLOAD: {local_path} -> {remote_path}")
```

La consola ya imprime el formato nuevo (`[{label}] UPLOAD  {fname:<40} OK`) directamente.
`all_stdout` queda vacío para uploads; no se usa para nada más en el runner remoto.

### ikctl/pipeline.py — Bug 2 (`_print_results`, líneas 72-77)

Los bloques de impresión de `result.stdout` y `result.stderr` se envolvieron con
`if self.options.debug:`:

```python
# ANTES:
for result in results:
    if result.stdout:
        for line in result.stdout.splitlines():
            _console.print(f"[cyan]{line}[/cyan]")
    if result.stderr:
        for line in result.stderr.splitlines():
            _error_console.print(f"[red]{line}[/red]")
    self.log.stdout(None, None, 0 if result.success else 1)

# DESPUÉS:
for result in results:
    if self.options.debug:
        if result.stdout:
            for line in result.stdout.splitlines():
                _console.print(f"[cyan]{line}[/cyan]")
        if result.stderr:
            for line in result.stderr.splitlines():
                _error_console.print(f"[red]{line}[/red]")
    self.log.stdout(None, None, 0 if result.success else 1)
```

## 3. Tests afectados

Ningún test requirió modificación:

- `tests/test_remote_runner.py`: ningún test verificaba que `result.stdout`
  contuviese el formato `UPLOAD: /path -> /path`. Los tests de consola
  (`test_upload_prints_ok_line`, etc.) comprueban la salida de `_console`,
  no `RunResult.stdout`.
- `tests/test_pipeline.py`: ningún test comprobaba que stdout/stderr se
  imprimieran sin `debug=True`; los tests verifican comportamiento de
  `sys.exit` y llamadas a mocks.

## 4. Resultado de pytest

```
270 passed, 1 warning in 0.85s
```
