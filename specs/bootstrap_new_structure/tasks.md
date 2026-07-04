# Tasks: bootstrap_new_structure

## Implementation tasks

- [ ] Add `_DEFAULT_CONFIG` string constant to `bootstrap.py` (YAML with all fields + comments)
- [ ] Add `_EXAMPLE_KIT` string constant to `bootstrap.py`
- [ ] Add `_EXAMPLE_PIPELINE` string constant to `bootstrap.py`
- [ ] Refactor `__init__` to define `_default_dir`, `_kits_dir`, `_pipelines_dir`, `_servers_dir`
- [ ] Replace `_ensure_kits_dir()` with `_ensure_default_dirs()` creating the three subdirs
- [ ] Update `_ensure_config_file()` to write `_DEFAULT_CONFIG` (string template, not yaml.dump)
- [ ] Update `_ensure_servers_yaml()` to write to `servers/config.yaml`
- [ ] Add `_ensure_secrets_file()` writing empty `servers/.secrets`
- [ ] Add `_ensure_example_kit()` creating `kits/example-kit/ikctl.yaml`
- [ ] Add `_ensure_example_pipeline()` creating `pipelines/example.yaml`
- [ ] Update `setup()` to call all new `_ensure_*` methods
- [ ] Replace all `open()` calls with `pathlib.Path.write_text()`

## Test tasks

- [ ] Update existing tests that reference old paths (`~/kits/config.yaml` → `~/kits/default/servers/config.yaml`)
- [ ] Add test: `example-kit/ikctl.yaml` created
- [ ] Add test: `pipelines/example.yaml` created
- [ ] Add test: `servers/.secrets` created
- [ ] Add test: config contains commented `timeout_connect` line
- [ ] Add test: config contains commented `kits_repo` line
- [ ] Run `uv run pytest tests/ -v` — all green
- [ ] Run `./init.sh` — ends with `[OK] Entorno listo`
