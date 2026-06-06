# ikctl — Install Kit Control

CLI tool to deploy and execute bash scripts ("kits") on remote servers via SSH/SFTP or on the local machine. Supports parallel execution, DAG-based pipeline orchestration, and git-based kit repositories.

## How it works

A **kit** is a folder containing bash scripts and an `ikctl.yaml` manifest. ikctl uploads the scripts to the remote server via SFTP and executes them over SSH.

A **pipeline** is a YAML file that chains multiple kits across different server groups, with dependencies, parallel execution and output passing between steps.

Everything is driven by `~/.ikctl/config`, which defines one or more **contexts** (server groups, kits source, secrets).

```
~/.ikctl/config          ← main config: contexts, active context
~/kits/
  config.yaml            ← server groups
  show-date/
    ikctl.yaml           ← kit manifest (uploads + pipeline + outputs)
    date.sh              ← the actual script
~/kits/pipelines/
  deploy.yaml            ← pipeline YAML
```

Kits are **auto-discovered** — no index file needed. Any folder under `path_kits` that contains an `ikctl.yaml` is a kit.

## Requirements

- Python 3.13+
- git (for git-based kit repositories)

## Installation

**Recommended — pipx** (isolated, no system conflicts):
```bash
pipx install ikctl
```

**With uv:**
```bash
uv tool install ikctl
```

**With pip** (on Debian/Ubuntu you may need `--break-system-packages`):
```bash
pip install ikctl --break-system-packages
```

**From source:**
```bash
git clone <repo>
cd ikctl
uv sync
uv run ikctl --version
```

## Initial setup

On first run, ikctl creates `~/.ikctl/` and `~/kits/` automatically.

Minimal `~/.ikctl/config`:

```yaml
context: production
contexts:
  production:
    path_kits: ~/kits               # where your kits live (auto-discovered)
    path_servers: ~/kits            # where config.yaml lives
    path_secrets: ~/.passwords/pw   # file containing the sudo/ssh password
    path_pipelines: ~/kits/pipelines # optional: pipelines directory
    mode: remote
    timeout_connect: 30.0           # SSH connect timeout (seconds)
    timeout_exec: 120.0             # local command timeout (seconds)
    exclude:                        # optional: kits to hide from discovery
      - internal/debug-kit
```

### Git-based kits (optional)

Pull kits from a git repository instead of a local directory:

```yaml
contexts:
  production:
    kits_repo: git@gitlab.com:company/kits.git   # SSH repo
    kits_ref: main                                # branch, tag or commit
    # kits_token: $GITLAB_TOKEN                  # for private HTTPS repos
    path_servers: ~/kits/production
    path_secrets: ~/.passwords/password
    mode: remote
```

For private HTTPS repos:
```yaml
    kits_repo: https://gitlab.com/company/kits.git
    kits_token: $GITLAB_TOKEN    # references an env variable
```

```bash
export GITLAB_TOKEN=glpat-xxxxxxxxxxxx
ikctl --list kits   # clones on first use, pulls on subsequent runs
```

## Server config

```yaml
# ~/kits/config.yaml
servers:
  - name: workers
    user: ubuntu
    hosts: [10.0.0.10, 10.0.0.11, 10.0.0.12]
    port: 22
    pkey: ~/.ssh/id_ed25519        # key-based auth

  - name: master
    user: ubuntu
    hosts: [10.0.0.5]
    port: 22
    pkey: ~/.ssh/id_ed25519

  - name: db
    user: root
    hosts: [10.0.0.20]
    port: 22
    password: $PASSWORD             # password auth (env var)
```

## SSH authentication

| Config key | Auth method | Notes |
|-----------|-------------|-------|
| `pkey: ~/.ssh/id_ed25519` | Public key only | Ed25519, ECDSA or RSA |
| `password: $PASSWORD` | Password only | |
| Neither | SSH agent + `~/.ssh/` discovery | |

`pkey` and `password` are mutually exclusive — only one is attempted.

## Kit structure

```yaml
# ~/kits/kubeadm-init/ikctl.yaml
kits:
  uploads:
    - kubeadm-init.sh     # files to upload to the remote server
  pipeline:
    - kubeadm-init.sh     # scripts to execute in order
  outputs:                # optional: documents KEY=VALUE the script emits
    JOIN_TOKEN: "kubeadm join token for worker nodes"
    JOIN_ENDPOINT: "API server endpoint (IP:6443)"
```

The `outputs:` field documents what `KEY=VALUE` lines the script writes to stdout. These values are available to subsequent pipeline steps via `{{ steps.<id>.KEY }}`.

## Usage

```
ikctl [-l {kits,servers,context,mode,pipelines}] [-i INSTALL] [-n NAME]
      [-p [PARAM ...]] [-s {sudo}] [-c CONTEXT] [-m {local,remote}]
      [-v] [--dry-run] [--debug] [--describe KIT]
      [--pipeline FILE] [--timeout-connect F] [--timeout-exec F]
      [--parallel-workers N]
```

### List

```bash
ikctl --list kits       # all discovered kits (shows declared outputs)
ikctl --list servers    # configured server groups
ikctl --list context    # active context and all paths
ikctl --list pipelines  # pipeline YAML files in path_pipelines
```

### Inspect a kit

```bash
ikctl --describe kubeadm-init
```

Shows the kit's scripts and declared outputs:
```
╭─ Kit ───────────────╮
│  kubeadm-init       │
╰─────────────────────╯
Uploads:  kubeadm-init.sh
Pipeline: kubeadm-init.sh
Outputs:
  JOIN_TOKEN    → kubeadm join token for worker nodes
  JOIN_ENDPOINT → API server endpoint (IP:6443)
```

### Switch context

```bash
ikctl --context staging
```

### Run a kit

```bash
# Remote (default)
ikctl --install show-date --name workers

# With parameters passed to the script
ikctl --install deploy --name workers -p v2.1.0

# With sudo
ikctl --install install-docker --name workers --sudo sudo

# Local machine (no SSH)
ikctl --install show-date --mode local

# Preview without executing
ikctl --install deploy --name workers -p v2.1.0 --dry-run
```

### Parallel execution

When a server group has multiple hosts, ikctl runs them concurrently:

```bash
ikctl --install show-date --name workers --parallel-workers 4
```

A spinner appears while connecting to each host and a progress bar during uploads. Output is prefixed with the host IP.

### Pipeline orchestration

A pipeline chains kits across server groups with DAG dependencies and output passing:

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
      - "{{ params.POD_CIDR }}"      # from CLI: -p POD_CIDR=192.168.0.0/16

  - id: join-workers
    kit: join-in-kubes
    servers: workers
    sudo: true
    needs: [init-master]
    params:
      - "{{ steps.init-master.JOIN_TOKEN }}"    # output from previous step
      - "{{ steps.init-master.JOIN_ENDPOINT }}" # output from previous step
```

```bash
# Run pipeline by name (requires path_pipelines in config)
ikctl --pipeline install-kubernetes -p POD_CIDR=192.168.0.0/16

# Or by full path
ikctl --pipeline ~/kits/pipelines/install-kubernetes.yaml -p POD_CIDR=192.168.0.0/16

# Preview
ikctl --pipeline install-kubernetes -p POD_CIDR=192.168.0.0/16 --dry-run
```

Steps without `needs` run in parallel. Steps fail gracefully — dependents are marked as `skipped`.

### Debug mode

```bash
# Show all internal logs (paramiko included)
ikctl --install show-date --name workers --debug
```

Without `--debug`, only useful output is shown (Rich formatted).

### Timeouts

```bash
ikctl --install show-date --name workers --timeout-connect 60
ikctl --install build --mode local --timeout-exec 300
```

Or set per context in `~/.ikctl/config` with `timeout_connect` and `timeout_exec`.

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.
