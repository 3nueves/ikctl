# Requirements: bootstrap_new_structure

## Goal
Improve `ConfigBootstrap` so that after running `setup()`, the user has a complete, working directory structure with example files and a fully documented config.

## Directory structure created

```
~/
├── .ikctl/
│   └── config              # all context fields, commented options, short comment per field
└── kits/
    └── default/
        ├── kits/
        │   └── example-kit/
        │       └── ikctl.yaml   # functional kit manifest
        ├── pipelines/
        │   └── example.yaml     # example orchestration pipeline
        └── servers/
            ├── config.yaml      # example server group
            └── .secrets         # empty secrets file
```

## Config file requirements

- Includes both `local` and `remote` contexts.
- Every field of the `Context` dataclass has a one-line comment explaining its purpose.
- Optional fields that are not commonly needed appear commented-out (prefixed with `#`).
- Active (uncommented) fields: `mode`, `path_kits`, `path_servers`, `path_secrets`, `path_pipelines`.
- Commented-out fields: `timeout_connect`, `timeout_exec`, `exclude`, `kits_repo`, `kits_ref`, `kits_token`.

## Code requirements

- All default dicts (`_DEFAULT_SERVERS`, config dict) must be module-level constants.
- `bootstrap.py` must not use `open()` directly; use `pathlib.Path.write_text()`.
- Idempotent: if a file already exists, do not overwrite it (existing behavior preserved).
- The `--force` flag (handled by `InitWizard`, not `ConfigBootstrap`) is out of scope here.
- No new external dependencies.
