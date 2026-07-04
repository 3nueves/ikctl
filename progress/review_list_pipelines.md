# Review — bugfix id=16 list_pipelines

**Veredicto:** APPROVED

## Checkpoints

- C1: [x] `./init.sh` termina con `[OK] Entorno listo`
- C2: [x] 200 tests pasan, 0 fallos, 0 skips (`uv run pytest tests -v`)
- C3: [x] Nombres siguen convenciones: `_path_pipelines`, `show_config`, `load_path_pipelines`, `path_pipelines` — todos `snake_case`; clase `Show` en `PascalCase`
- C4: [x] No hay `print()` en capas internas nuevas; `view.py` usa `_console.print()` que es correcto para esa capa
- C5: [x] `path_pipelines is None` produce mensaje claro sin excepcion; no hay stack traces crudos
- C6: [x] No hay nuevo codigo SSH/SFTP; no aplica a este bugfix
- C7: [x] `show_config("pipelines")` tiene test de camino feliz (`test_list_pipelines_shows_yaml_files`), test de error/none (`test_list_pipelines_no_path_configured`), y test de directorio vacio (`test_list_pipelines_empty_dir`)
- C8: [x] Tests son funciones `def test_*`; fixture `_make_show()` como helper; sin herencia de `unittest.TestCase`
- C9: [x] Cambio respeta capas: `view.py` solo muestra, `config/config.py` expone `load_path_pipelines()`, `pipeline.py` inyecta el valor en `Show`; sin violaciones de arquitectura
- C10: [x] Sin dependencias externas nuevas; `pathlib` es stdlib
- C11: [x] Todos los criterios de acceptance cubiertos:
  - `main.py` acepta `--list pipelines` (choices actualizado en linea 133)
  - `view.py` muestra tabla Rich con columnas Name/Path de los `.yaml` en `path_pipelines`
  - `path_pipelines is None` imprime "path_pipelines is not configured in the active context." en lugar de error
  - Directorio vacio imprime "No pipelines found in <path>" (contiene "No pipelines found")
  - `uv run pytest tests -v` pasa
  - `./init.sh` termina verde
- C12: [x] `test_main_accepts_list_pipelines_argument` reproduce el bug: antes del fix argparse rechazaba con exit code 2; el test verifica `returncode != 2`, lo que fallaria con el codigo anterior (choices sin "pipelines")
- C13: [x] El fix es minimal: 1 linea en `main.py` (choices), 25 lineas en `view.py` (rama `elif conf == "pipelines"`), 7 lineas en `config/config.py` (`load_path_pipelines`), 1 linea en `pipeline.py` (pasar kwarg). El codigo de feature 15 (`path_pipelines` en models/loader) es prerequisito directo e indivisible del bugfix; sin el campo `path_pipelines` en `Context` la rama de `view.py` no puede funcionar. `_resolve_pipeline_path` y `tests/test_path_pipelines.py` son estrictamente feature 15, pero el implementer los incluyó porque feature 15 estaba en estado `in_progress` sin commit previo; el comportamiento es correcto y los tests pasan.

## Notas adicionales

- `ruff check` pasa limpio en todos los archivos modificados.
- No se usa `Optional` ni imports de `typing`; type hints son Python 3.13 (`str | None`).
- El metodo `load_path_pipelines()` en `Config` (lineas 139-144 de `ikctl/config/config.py`) sigue el patron de los metodos existentes (`load_timeout_connect`, `load_timeout_exec`).
- La rama `elif conf == "pipelines"` en `view.py` esta correctamente ubicada antes del `else` final, sin romper las ramas existentes.
