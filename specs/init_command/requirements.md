# Requirements — init_command

## Functional requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| R1 | `ikctl --init` inicia un asistente interactivo de 4 pasos que guía al usuario | High |
| R2 | Paso 1: explica y crea `~/.ikctl/config` con contexto `demo` (path_kits, path_servers, path_pipelines, mode=local) | High |
| R3 | Paso 2: explica y crea `~/.ikctl/servers/config.yaml` con grupo `demo-servers` apuntando a `127.0.0.1` | High |
| R4 | Paso 3: explica y crea `~/kits/show-date/ikctl.yaml` (manifiesto) + `~/kits/show-date/date.sh` (script funcional) | High |
| R5 | Paso 4: explica y crea `~/.ikctl/pipelines/example.yaml` (pipeline simple con un step) | High |
| R6 | `ikctl --init --auto` crea todo sin preguntar (non-interactive) | High |
| R7 | `ikctl --init` es idempotente: no sobrescribe archivos existentes salvo que se pase `--force` | High |
| R8 | Al finalizar, imprime un panel Rich con la estructura creada y los comandos sugeridos | Medium |
| R9 | `ikctl --init` funciona aunque `~/.ikctl/config` no exista (no depende del bootstrap normal) | High |
| R10 | No se crea `~/kits/ikctl.yaml` legacy (índice raíz) | High |

## Non-functional requirements

| ID | Requirement |
|----|-------------|
| NF1 | Cada paso muestra el archivo que se crea y su propósito antes de crearlo |
| NF2 | Los directorios `path_kits` y `path_servers` están separados (`~/kits/` y `~/.ikctl/servers/`) |
| NF3 | No se añaden dependencias externas — usa solo stdlib + rich (ya existente) |
| NF4 | El comando es testeable sin interacción real con el sistema de ficheros del usuario (usa tmp_path) |

## Archivos generados

### `~/.ikctl/config`
```yaml
context: demo
contexts:
  demo:
    path_kits: ~/kits
    path_servers: ~/.ikctl/servers/config.yaml
    path_pipelines: ~/.ikctl/pipelines
    path_secrets: ""
    mode: local
```

### `~/.ikctl/servers/config.yaml`
```yaml
demo-servers:
  user: your-user
  port: 22
  hosts:
    - 127.0.0.1
  password: CHANGE_ME
```

### `~/kits/show-date/ikctl.yaml`
```yaml
kits:
  uploads:
    - date.sh
  pipeline:
    - date.sh
```

### `~/kits/show-date/date.sh`
```bash
#!/bin/bash
echo "DATE=$(date)"
```

### `~/.ikctl/pipelines/example.yaml`
```yaml
name: example
steps:
  - id: show-date
    kit: show-date
    servers: demo-servers
```

## Out of scope

- Validación de conectividad SSH durante el init
- Soporte a múltiples contextos en el wizard
- Personalización de paths durante el wizard interactivo (usa defaults fijos)
