# Design: bootstrap_new_structure

## Changes to bootstrap.py

### Module-level constants

```python
_DEFAULT_SERVERS: dict = { ... }          # already exists, keep as-is
_DEFAULT_CONFIG: str = """..."""           # new: YAML string with all fields + comments
_EXAMPLE_KIT: str = """..."""             # new: ikctl.yaml content for example-kit
_EXAMPLE_PIPELINE: str = """..."""        # new: example.yaml pipeline content
```

Using a multiline string for `_DEFAULT_CONFIG` instead of `yaml.dump()` allows embedding YAML comments, which `yaml.dump()` cannot produce.

### New directory layout in `__init__`

```python
self._default_dir      = self._home / "kits" / "default"
self._kits_dir        = self._default_dir / "kits"
self._pipelines_dir   = self._default_dir / "pipelines"
self._servers_dir     = self._default_dir / "servers"
```

### `setup()` method — new sequence

1. `_ensure_ikctl_dir()`
2. `_ensure_default_dirs()`   — creates kits/, pipelines/, servers/ under default/
3. `_ensure_config_file()`   — writes ~/.ikctl/config using _DEFAULT_CONFIG
4. `_ensure_servers_yaml()`  — writes servers/config.yaml using _DEFAULT_SERVERS
5. `_ensure_secrets_file()`  — writes servers/.secrets (empty)
6. `_ensure_example_kit()`   — writes kits/example-kit/ikctl.yaml
7. `_ensure_example_pipeline()` — writes pipelines/example.yaml

### Each `_ensure_*` method pattern

```python
def _ensure_foo(self) -> None:
    path = self._foo_path
    if path.exists():
        return
    if not path.parent.exists():
        return
    path.write_text(_FOO_CONTENT, encoding="utf-8")
    _logger.info("Created: %s", path)
```

### Config file format (YAML with comments)

Since `yaml.dump()` strips comments, `_DEFAULT_CONFIG` is a plain string template with `{kits_path}`, `{servers_path}`, `{pipelines_path}` placeholders filled via `.format()` at write time.

## Changes to test_bootstrap.py

Add tests for:
- `~/kits/default/kits/example-kit/ikctl.yaml` is created
- `~/kits/default/pipelines/example.yaml` is created
- `~/kits/default/servers/config.yaml` is created
- `~/kits/default/servers/.secrets` is created
- `~/.ikctl/config` contains all expected keys (`timeout_connect`, `kits_repo`, etc.) as commented lines
- Existing tests for idempotence and placeholder still pass
