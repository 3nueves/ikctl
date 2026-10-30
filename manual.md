# Manual de ikctl

> **ikctl** (Install Kit Control) — versión 1.12.2

## 1. ¿Para qué sirve?

`ikctl` es una herramienta de línea de comandos (CLI) para **desplegar y ejecutar
scripts de bash ("kits") en servidores remotos vía SSH/SFTP o en la máquina local**.

Sus capacidades principales son:

- **Ejecución remota o local** de scripts sin configurar nada por servidor.
- **Ejecución en paralelo** sobre varios hosts de un mismo grupo.
- **Orquestación por pipelines** (grafos de dependencias o DAG) que encadenan
  varios kits sobre distintos grupos de servidores, pasando salidas entre pasos.
- **Kits desde repositorios git**, con soporte de ramas, tags y tokens.
- **Modo simulación** (`--dry-run`) para previsualizar sin ejecutar nada.

### Conceptos clave

| Término       | Significado                                                                 |
|---------------|-----------------------------------------------------------------------------|
| **Kit**       | Carpeta con scripts bash y un manifiesto `ikctl.yaml`.                       |
| **Pipeline**  | Archivo YAML que encadena varios kits con dependencias y paralelismo.        |
| **Contexto**  | Conjunto de configuración (grupo de servidores, ruta de kits, secretos).     |
| **Servidor**  | Grupo de hosts definido en `config.yaml` (usuario, IPs, puerto, auth).       |

Los kits se **descubren automáticamente**: cualquier carpeta bajo `path_kits`
que contenga un `ikctl.yaml` es un kit. No hay índice.

## 2. Tecnología

- **Lenguaje:** Python **3.13+**.
- **SSH/SFTP:** [paramiko](https://www.paramiko.org/) (`>=3.0,<4.0`).
- **YAML:** `pyaml` y `envyaml` (permite interpolar variables de entorno).
- **Interfaz de terminal:** [Rich](https://github.com/Textualize/rich) (paneles,
  tablas, barras de progreso, colores).
- **Empaquetado:** `hatchling` + `uv`.
- **Licencia:** Apache 2.0.

Arquitectura por capas con interfaces (`IRunner`, `IConnection`, `IExecutor`),
lo que permite añadir otros ejecutores (Docker, Ansible…) sin tocar el orquestador.

## 3. Instalación

**Recomendado — pipx** (aislado, sin conflictos):
```bash
pipx install ikctl
```

**Con uv:**
```bash
uv tool install ikctl
```

**Con pip** (en Debian/Ubuntu puede requerir `--break-system-packages`):
```bash
pip install ikctl --break-system-packages
```

**Script de instalación** (pip `--user` + arreglo automático del PATH):
```bash
bash install.sh
```

**Desde el código fuente:**
```bash
git clone <repo>
cd ikctl
uv sync
uv run ikctl --version
```

## 4. Configuración inicial

En la primera ejecución se crean `~/.ikctl/` y `~/kits/` automáticamente.
También existe un asistente interactivo:

```bash
ikctl --init          # crea config, servidores, kit y pipeline de ejemplo
ikctl --init --auto   # sin preguntas (no interactivo)
ikctl --init --force  # sobrescribe archivos existentes
```

### Configuración principal — `~/.ikctl/config`

```yaml
context: production
contexts:
  production:
    path_kits: ~/kits                 # dónde viven los kits (auto-descubiertos)
    path_servers: ~/kits              # dónde está config.yaml
    path_secrets: ~/.passwords/pw     # archivo con la contraseña sudo/ssh
    path_pipelines: ~/kits/pipelines  # opcional: directorio de pipelines
    mode: remote
    timeout_connect: 30.0             # timeout de conexión SSH (segundos)
    timeout_exec: 120.0               # timeout de ejecución local (segundos)
    exclude:                          # opcional: kits ocultos
      - internal/debug-kit
```

### Kits desde git (opcional)

```yaml
contexts:
  production:
    kits_repo: git@gitlab.com:company/kits.git  # repositorio SSH
    kits_ref: main                              # rama, tag o commit
    # kits_token: $GITLAB_TOKEN                 # para repos HTTPS privados
    path_servers: ~/kits/production
    path_secrets: ~/.passwords/password
    mode: remote
```

### Servidores — `~/kits/config.yaml`

```yaml
servers:
  - name: workers
    user: ubuntu
    hosts: [10.0.0.10, 10.0.0.11, 10.0.0.12]
    port: 22
    pkey: ~/.ssh/id_ed25519     # autenticación con clave

  - name: master
    user: ubuntu
    hosts: [10.0.0.5]
    port: 22
    pkey: ~/.ssh/id_ed25519

  - name: db
    user: root
    hosts: [10.0.0.20]
    port: 22
    password: $PASSWORD          # autenticación con contraseña (desde env var)
```

### Autenticación SSH

| Config                        | Método                              |
|-------------------------------|-------------------------------------|
| `pkey: ~/.ssh/id_ed25519`     | Solo clave pública (Ed25519/ECDSA/RSA) |
| `password: $PASSWORD`         | Solo contraseña                     |
| Ninguno de los dos            | Agente SSH + `~/.ssh/`              |

`pkey` y `password` son mutuamente excluyentes.

## 5. Estructura de un kit

```yaml
# ~/kits/kubeadm-init/ikctl.yaml
kits:
  uploads:
    - kubeadm-init.sh     # archivos a subir al servidor remoto
  pipeline:
    - kubeadm-init.sh     # scripts a ejecutar en orden
  outputs:                # opcional: documenta las líneas KEY=VALUE que emite
    JOIN_TOKEN: "kubeadm join token para nodos worker"
    JOIN_ENDPOINT: "endpoint del API server (IP:6443)"
```

Las salidas (`outputs`) quedan disponibles en pasos posteriores de un pipeline
mediante `{{ steps.<id>.KEY }}`.

## 6. Uso

```
ikctl [-l {kits,servers,context,mode,pipelines}] [-i INSTALL] [-n NAME]
      [-p [PARAM ...]] [-s {sudo}] [-c CONTEXT] [-m {local,remote}]
      [-v] [--dry-run] [--debug] [--describe KIT]
      [--pipeline FILE] [--init] [--stdout] [--stderr] [--strict]
      [--timeout-connect F] [--timeout-exec F] [--parallel-workers N]
```

### Listar

```bash
ikctl --list kits        # kits descubiertos (muestra las salidas declaradas)
ikctl --list servers     # grupos de servidores configurados
ikctl --list context     # contexto activo y rutas
ikctl --list pipelines   # pipelines en path_pipelines
ikctl --list mode        # modo activo
```

### Inspeccionar un kit

```bash
ikctl --describe kubeadm-init
```

### Cambiar de contexto

```bash
ikctl --context staging
```

### Ejecutar un kit

```bash
# Remoto (por defecto)
ikctl --install show-date --name workers

# Con parámetros pasados al script
ikctl --install deploy --name workers -p v2.1.0

# Con sudo
ikctl --install install-docker --name workers --sudo sudo

# En la máquina local (sin SSH)
ikctl --install show-date --mode local

# Previsualizar sin ejecutar
ikctl --install deploy --name workers -p v2.1.0 --dry-run
```

### Ejecución en paralelo

Cuando un grupo tiene varios hosts, ikctl los ejecuta concurrentemente:

```bash
ikctl --install show-date --name workers --parallel-workers 4
```

### Orquestación con pipelines

```yaml
# ~/kits/pipelines/install-kubernetes.yaml
name: install-kubernetes

steps:
  - id: prepare
    kit: packages
    servers: all-nodes
    sudo: true

  - id: init-master
    kit: kubeadm-init
    servers: master
    sudo: true
    needs: [prepare]
    params:
      - "{{ params.POD_CIDR }}"               # desde CLI: -p POD_CIDR=192.168.0.0/16

  - id: join-workers
    kit: join-in-kubes
    servers: workers
    sudo: true
    needs: [init-master]
    params:
      - "{{ steps.init-master.JOIN_TOKEN }}"       # salida del paso anterior
      - "{{ steps.init-master.JOIN_ENDPOINT }}"    # salida del paso anterior
```

```bash
# Por nombre (requiere path_pipelines en la config)
ikctl --pipeline install-kubernetes -p POD_CIDR=192.168.0.0/16

# Por ruta completa
ikctl --pipeline ~/kits/pipelines/install-kubernetes.yaml -p POD_CIDR=192.168.0.0/16

# Previsualizar
ikctl --pipeline install-kubernetes -p POD_CIDR=192.168.0.0/16 --dry-run
```

Los pasos sin `needs` se ejecutan en paralelo. Si un paso falla, sus dependientes
se marcan como `skipped`.

### Ejecución directa sobre hosts concretos

Sin pasar por `config.yaml`:

```bash
ikctl --install show-date -n x \
  --host 10.0.0.10 --host 10.0.0.11 \
  --user ubuntu --key ~/.ssh/id_ed25519
```

### Opciones útiles

| Opción                 | Descripción                                              |
|------------------------|----------------------------------------------------------|
| `--debug`              | Logs internos completos (incluye paramiko).              |
| `--stdout`             | Muestra la salida stdout de los scripts.                 |
| `--stderr`             | Muestra stderr en caso de fallo.                         |
| `--strict`             | Ejecuta con `bash -eo pipefail`.                         |
| `--force-upload`       | Sube todos los archivos, saltando verificación SHA256.   |
| `--remote-dir DIR`     | Directorio remoto de subida (sobrescribe el del kit).    |
| `--sudo-password PASS` | Contraseña para sudo.                                    |
| `--timeout-connect F`  | Timeout de conexión SSH (segundos).                      |
| `--timeout-exec F`     | Timeout de ejecución local (segundos).                   |

## 7. Ejemplo rápido de principio a fin

```bash
# 1. Instalar
pipx install ikctl

# 2. Configuración guiada
ikctl --init

# 3. Ver qué hay
ikctl --list kits
ikctl --list servers

# 4. Inspeccionar un kit
ikctl --describe show-date

# 5. Ejecutarlo remotamente en el grupo "workers"
ikctl --install show-date --name workers

# 6. Igual pero en local
ikctl --install show-date --mode local
```

## 8. Referencia de archivos

```
~/.ikctl/config                 ← configuración principal: contextos, contexto activo
~/kits/
  config.yaml                   ← grupos de servidores
  show-date/
    ikctl.yaml                  ← manifiesto del kit (uploads + pipeline + outputs)
    date.sh                     ← el script real
  pipelines/
    deploy.yaml                 ← pipeline YAML
```

## 9. Licencia

Apache License 2.0 — ver [LICENSE](LICENSE).
