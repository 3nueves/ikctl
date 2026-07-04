# Design — ansible_style_output

## Cambios por fichero

### `ikctl/runner/remote.py`

#### 1. Eliminar imports de Rich Progress
```python
# ELIMINAR:
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
```

#### 2. Añadir `debug` a `RunOptions` o leerlo desde options
`RunOptions` ya tiene `dry_run: bool`. Se añade `debug: bool = False` si no
existe, o se lee de `options.debug` si ya está disponible.

> **Nota**: Verificar si `RunOptions` ya tiene `debug`. Si no, añadirlo.

#### 3. Reemplazar el bloque `with Progress(...)` en `_run_on_host()`

**Antes:**
```python
with Progress(...) as progress:
    for local_path in kit.uploads:
        task = progress.add_task(...)
        sftp.upload(local_path, remote_path)
        progress.update(task, completed=file_size)
        all_stdout.append(f"[{host}] UPLOAD: ...")
```

**Después:**
```python
for local_path in kit.uploads:
    fname = os.path.basename(local_path)
    try:
        sftp.upload(local_path, remote_path)
        _console.print(f"[{label}] UPLOAD  {fname:<40} OK")
    except Exception as exc:
        _console.print(f"[{label}] UPLOAD  {fname:<40} FAILED")
        raise
```

#### 4. Reemplazar logging de RUN por línea de consola

**Antes:**
```python
stdout, stderr, exit_code = executor.execute(full_cmd)
for line in stdout.splitlines():
    all_stdout.append(f"[{host}] {line}")
```

**Después:**
```python
stdout, stderr, exit_code = executor.execute(full_cmd)
status = "OK" if exit_code == 0 else "FAILED"
_console.print(f"[{label}] RUN     {script:<40} {status}")
if options.debug:
    for line in stdout.splitlines():
        _console.print(f"[{label}] {line}")
    for line in stderr.splitlines():
        _console.print(f"[{label}] {line}", stderr=True)
```

#### 5. `label` en `_run_on_host()`
```python
# Al inicio del método, derivar el label:
label = host  # fallback — siempre disponible
# No se pasa el nombre del servidor a este nivel todavía;
# se usa el host (IP o hostname) como label.
# RF-4 queda satisfecho parcialmente: la IP es el identificador disponible.
# El nombre completo requeriría pasar ServerGroup con nombres, fuera de scope.
```

> **Decisión de diseño**: `ServerGroup` no tiene campo `name` por servidor
> individual (solo tiene `hosts: list[str]`). El label será el host (IP o
> hostname). Esto satisface la intención — no se mezclan con logs de paramiko —
> aunque no sea un nombre legible. Añadir nombres por host es feature futura.

### `ikctl/runner/base.py`

Verificar si `RunOptions` tiene campo `debug`. Si no existe, añadirlo:
```python
debug: bool = False
```

### `ikctl/main.py`

Añadir `debug=args.debug` al constructor de `RunOptions` en el bloque de
construcción `run_options = RunOptions(...)`.

## Ficheros NO modificados

- `ikctl/runner/local.py`
- `ikctl/runner/dry_run.py`
- `ikctl/transfer/sftp.py`
- `ikctl/pipeline.py`

## Tests

### `tests/test_remote_runner.py` — tests nuevos o modificados

1. **`test_upload_line_format`**: capturar stdout de `_console`, verificar que
   contiene `UPLOAD` y `OK` para un upload exitoso.
2. **`test_run_line_format`**: verificar que contiene `RUN` y `OK`.
3. **`test_no_host_stdout_without_debug`**: sin `debug=True`, el stdout del
   host no aparece en la salida.
4. **`test_host_stdout_with_debug`**: con `debug=True`, el stdout del host sí
   aparece.
5. Tests existentes deben seguir pasando.
