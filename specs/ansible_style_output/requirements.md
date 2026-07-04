# Requirements — ansible_style_output

## Contexto

La salida actual de `ikctl` al instalar un kit mezcla barras de progreso Rich,
IPs de host y logs de paramiko, resultando en una UI caótica. El objetivo es
una salida limpia y predecible al estilo Ansible: una línea por acción, con
estado explícito al final, y sin ruido.

## Requisitos funcionales

### RF-1: Eliminar barra de progreso
La barra de progreso (`rich.progress.Progress`) se elimina del runner remoto.
No se reemplaza por ningún spinner. La subida de ficheros produce una sola
línea por fichero.

### RF-2: Formato de líneas UPLOAD
Cada fichero subido produce exactamente una línea:
```
[<label>] UPLOAD  <nombre_fichero>           OK
[<label>] UPLOAD  <nombre_fichero>           FAILED
```

### RF-3: Formato de líneas RUN
Cada paso del pipeline produce exactamente una línea:
```
[<label>] RUN     <nombre_script>            OK
[<label>] RUN     <nombre_script>            FAILED
```

### RF-4: Label del host
El `<label>` es el **nombre del servidor** (`-n <name>`), no la IP. Si no hay
nombre disponible, se usa el hostname/IP tal como viene en la lista de hosts.

### RF-5: Stdout/stderr del host
- Sin `--debug`: no se imprime stdout ni stderr del host remoto.
- Con `--debug`: stdout y stderr se imprimen con el prefijo `[<label>]`.

### RF-6: Resumen final
El resumen `N hosts OK, M hosts FAILED` se mantiene tal cual.

### RF-7: Comportamiento sin cambios en dry-run y local runner
`DryRunRunner` y `LocalRunner` no se modifican en este feature.

## Requisitos no funcionales

- El cambio no debe alterar la lógica de ejecución ni el manejo de errores.
- Los imports de `rich.progress` (BarColumn, Progress, etc.) deben eliminarse
  si ya no se usan.
- Compatible con ejecución multi-host paralela (ThreadPoolExecutor).
