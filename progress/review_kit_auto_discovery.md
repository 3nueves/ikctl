# Review — feature 9 (kit_auto_discovery)

**Veredicto:** APPROVED

## Checkpoints

- C1: [x] — `./init.sh` termina con `[OK] Entorno listo`
- C2: [x] — 136 tests pasan, 0 fallidos, 0 skips
- C3: [x] — Nombres siguen convenciones: `snake_case` en funciones/variables, `PascalCase` en clases; `_discover_manifests` correctamente prefijado con `_`
- C4: [x] — `KitRepository.__init__` usa `self._logger = logging.getLogger(__name__)`; `loader.py` usa `_logger = logging.getLogger(__name__)` a nivel de modulo; sin `print()` en capas internas
- C5: [x] — Las capas internas lanzan `KitNotFoundError` y `ConfigError`; solo `Pipeline`/`Config` llaman a `sys.exit()`
- C6: [x] — No hay SSH/SFTP en los archivos modificados; tests de `test_kit_repo.py` usan `tmp_path` de pytest sin conexiones reales
- C7: [x] — `resolve()` tiene happy path (`test_resolve_discovers_kit_without_index`, `test_resolve_nested_kit`) y error path (`test_resolve_raises_kit_not_found`, `test_resolve_excludes_kit_from_list`); `list_kits()` tiene happy path y edge cases (path inexistente, exclude)
- C8: [x] — Todos los tests son funciones `def test_*`; fixtures de pytest (`tmp_path`); sin herencia de `unittest.TestCase`
- C9: [x] — `KitRepository` vive en `ikctl/config/kit_repo.py` como indica `docs/architecture.md`; no cruza capas prohibidas; `exclude` anadido a `Context` en `models.py`
- C10: [x] — No se añaden dependencias externas; `yaml` usado en tests es stdlib-compatible via `PyYAML` que ya era transitiva
- C11: [x] — Los 7 criterios de acceptance se cumplen:
  1. `KitRepository.resolve()` usa `pathlib.Path(path_kits).rglob("ikctl.yaml")` — verificado en `kit_repo.py` lineas 23-26
  2. Nombre del kit es `str(p.parent.relative_to(path_kits))` — linea 53
  3. Raiz ignorada: `p.parent != path_kits` — linea 24, cubierto por `test_resolve_ignores_root_ikctl_yaml`
  4. Campo `exclude: list[str] = field(default_factory=list)` en `Context` — `models.py` linea 37; leido en `loader.py` lineas 45-54
  5. `--list kits` usa `Config.load_config_file_kits()` que delega a `KitRepository.list_kits()` — `config.py` lineas 75-78; `pipeline.py` linea 33
  6. `KitNotFoundError` lanzado cuando el nombre no coincide — `kit_repo.py` linea 80; cubierto por `test_resolve_raises_kit_not_found`
  7. Tests requeridos todos presentes y verdes: `test_resolve_discovers_kit_without_index`, `test_resolve_nested_kit`, `test_resolve_excludes_kit_from_list`, `test_resolve_ignores_root_ikctl_yaml`, `test_resolve_raises_kit_not_found`

## Notas adicionales

- `Context` es `frozen=True` con `exclude: list[str] = field(default_factory=list)`: correcto uso de `field()` para evitar mutable default en dataclass frozen.
- Type hints usan sintaxis Python 3.13 (`list[str]`, `str | None`); sin `Optional`/`List` de `typing`.
- `_discover_manifests` correctamente definido como metodo privado (prefijo `_`).
- `extract_config_kits` en `config.py` delega a `KitRepository.resolve()` preservando firma compatible con `pipeline.py`.
- Todos los tests anteriores (128 previos) siguen pasando sin modificacion.
