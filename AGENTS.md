# AGENTS.md — ikctl

Guidelines for agentic coding agents working in this repository.

---

## Project Overview

`ikctl` is a Python CLI tool for running "kits" (shell script collections) on remote servers via SSH or locally. It uses `paramiko` for SSH, `envyaml` for YAML config parsing, and Python's `argparse` for the CLI.

- **Language:** Python 3.10+ (targets 3.12)
- **Version:** defined in `ikctl/config/config.py` → `__version__`
- **Entry point:** `ikctl.main:main` (installed console script)
- **Package manager:** Pipenv (`Pipfile` / `Pipfile.lock`)

---

## Directory Structure

```
ikctl/                    ← project root
├── main.py               ← dev entry point (absolute imports)
├── setup.py              ← packaging; reads version from config.py
├── Pipfile               ← runtime + dev dependencies
└── ikctl/                ← main package
    ├── main.py           ← installed entry point (relative imports)
    ├── pipeline.py       ← top-level orchestrator
    ├── commands.py       ← SSH + local shell execution
    ├── execute.py        ← command builder (sudo / params variants)
    ├── context.py        ← context management (~/.ikctl/config)
    ├── view.py           ← listing / display logic
    ├── logs.py           ← colored terminal output helper
    ├── config/           ← Config class, version, first-run wizard
    ├── local/            ← RunLocalKits
    └── remote/           ← Connection, RunRemoteKits, Sftp
```

---

## Build & Install Commands

```bash
# Install all dependencies (from Pipfile)
pipenv install

# Editable install for local development
pip install -e .

# Build source distribution
python setup.py sdist

# Publish to PyPI
twine upload dist/*
```

---

## Running the CLI

```bash
ikctl -l kits                              # list available kits
ikctl -l servers                           # list configured servers
ikctl -l context                           # list saved contexts
ikctl -i <kit-name> -n <server-name>       # run kit on remote server
ikctl -i <kit-name> -n <server-name> -s sudo   # run with sudo
ikctl -i <kit-name> -n <server-name> -p p1 p2  # with parameters
ikctl -m local -i <kit-name>               # run kit locally
ikctl -c <context-name>                    # switch context
ikctl -v                                   # print version
```

---

## Linting & Formatting

**Formatter: Black** (configured in PyCharm `.idea/misc.xml`; no standalone config file).

```bash
# Format the package
black ikctl/

# Format a single file
black ikctl/pipeline.py
```

No linter (flake8, pylint, ruff, mypy) is configured at the repository level. When adding tooling, prefer `pyproject.toml` over standalone config files.

---

## Testing

**There is currently no test suite.** No `tests/` directory, no pytest configuration, and no test dependencies exist. When adding tests:

- Use `pytest` as the test framework.
- Place tests in a `tests/` directory mirroring the package structure.
- Name test files `test_<module>.py` and test functions `test_<description>`.

```bash
# Run all tests (once a test suite exists)
pytest

# Run a single test file
pytest tests/test_pipeline.py

# Run a single test function
pytest tests/test_pipeline.py::test_init_dispatches_remote

# Run with verbose output
pytest -v
```

---

## Code Style Guidelines

### Imports

Follow this order, separated by blank lines:

```python
# 1. Standard library
import logging
import os
import sys

# 2. Third-party
import paramiko
from envyaml import EnvYAML

# 3. Local / relative
from .logs import Log
from .config.config import Config
```

Relative imports (`.module`) are used everywhere inside the `ikctl/` package. The top-level `main.py` uses absolute imports (`from ikctl.pipeline import Pipeline`) for development convenience only.

### Naming Conventions

| Category | Convention | Example |
|---|---|---|
| Files | `snake_case.py` | `remote_kits.py`, `create_config_files.py` |
| Classes | `PascalCase` | `Pipeline`, `RunRemoteKits`, `Connection` |
| Methods / functions | `snake_case` | `run_kits()`, `open_conn()`, `load_config_file_kits()` |
| Private methods | `__double_underscore` prefix | `__create_folder_and_config_file()` |
| Instance variables | `snake_case` | `self.path_kits`, `self.config_servers` |
| Module-level version | dunder | `__version__ = "v0.6.1"` |

### Type Hints

Type hints are used partially. When adding or modifying code:

- Annotate all public method signatures (`def __init__(...) -> None:`).
- Use specific types over `object` where possible (`paramiko.SSHClient` instead of `object`).
- Prefer built-in generics (`list[str]`, `dict[str, str]`) over `typing.List` / `typing.Dict` (Python 3.10+).
- Avoid `Optional` — use `X | None` syntax instead.

Example of the existing style:

```python
def __init__(self, servers: dict, name_kit: str, kits: list,
             pipe: list, sftp: object, exe: object,
             log: object, options: object, secrets: str) -> None:
```

### Logger Pattern

Every class uses this idiom — preserve it:

```python
name = __name__.split(".")
self.name = name[-1]
self.logger = logging.getLogger(self.name)
```

### Formatting

- Black defaults (line length 88, double quotes).
- No trailing commas mandated — Black will enforce on format.
- Avoid lines longer than 88 characters.

---

## Error Handling

The established pattern is **try/except with print + exit** for user-facing failures:

```python
try:
    self.config = EnvYAML(self.path_config_file, strict=False)
except ValueError as error:
    print(f'\n--- {error} ---\n')
    exit()
except Exception as e:
    print("\n", e)
    sys.exit()
```

Rules:
- Catch **specific** exception types before a broad `Exception` fallback.
- Print a human-readable message before exiting.
- Use `sys.exit()` consistently (avoid bare `exit()` in new code).
- Do not silently swallow exceptions — always log or print.
- SSH-specific errors use `paramiko.SSHException`.

Colored output for success/failure uses ANSI codes via `logs.py`:

```python
self.log.success("message")   # green
self.log.error("message")     # red
```

---

## Architecture Patterns

### Dependency Injection

`Pipeline` (`ikctl/pipeline.py`) instantiates all collaborators and injects them via constructors. Do not import and instantiate collaborators inside lower-level modules.

```python
# Correct — receive dependencies via constructor
class RunRemoteKits:
    def __init__(self, ..., exe: object, log: object, ...):
        self.exe = exe
        self.log = log
```

### Orchestration

Routing logic lives in `Pipeline.init()`. New execution modes should be added as new classes (following `RunRemoteKits` / `RunLocalKits`) and wired in `Pipeline`.

### Configuration

- User config: `~/.ikctl/config` (YAML, loaded via `EnvYAML`)
- Kit scripts: `~/kits/` (path configurable)
- Version: single source of truth at `ikctl/config/config.py:__version__` — `setup.py` reads it dynamically; update only there.

### Dual Entry Points

- `main.py` (project root) — development/script use; uses absolute imports.
- `ikctl/main.py` — installed console script; uses relative imports. Keep both in sync.

---

## Known Issues (Do Not Regress)

- `ikctl/config/config.py` ~line 89: a `NameError` risk where `error` may be referenced outside its `except` scope — fix carefully, do not spread the pattern.
- Method names with typos exist in production code (`extrac_config_kits`, `extrac_secrets`, `change_permisions`) — do not rename without updating all call sites.
- `exit()` vs `sys.exit()` used inconsistently — prefer `sys.exit()` in new code.
