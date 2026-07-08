# Tasks — cli_defined_server

## Implementation

1. `ikctl/main.py`:
   - [x] Añadir argparse: `--host` (append), `--user`, `--password`, `--port`, `--key`
   - [x] Añadir bloque `if args.host:` que construye `ServerGroup` y asigna secrets/config_mode/timeouts/sudo_password
   - [x] Mantener el bloque `else:` con el flujo de carga YAML actual intacto

2. `tests/test_cli_defined_server.py`:
   - [x] `TestHostFlag`: 7 tests (creación, password, key, múltiples hosts, defaults)
   - [x] `TestBuildRunnerWithCLIServer`: 5 tests (build, connection factory, dry-run, local, parallel)
   - [x] `TestSudoPasswordResolutionWithHost`: 6 tests (precedencia, fallbacks)

## Verification

- [x] `uv run pytest tests/test_cli_defined_server.py -v` → 18 passed
- [x] `uv run pytest tests -v` → 314 passed (no regresiones)
- [x] `./init.sh` → verde