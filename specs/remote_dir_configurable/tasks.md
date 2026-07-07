# Implementation tasks — remote_dir_configurable

> Ordered list. Complete each task before starting the next.
> Update [ ] to [x] as you go. Document blockers in progress/current.md.

- [x] T1: Añadir `remote_dir: str | None = None` a `KitPipeline` en `ikctl/config/models.py`
- [x] T2: Leer `kits.remote_dir` en `kit_repo.py` y pasarlo a `KitPipeline`
- [x] T3: Añadir `remote_dir: str | None = None` a `RunOptions` en `ikctl/runner/base.py`
- [x] T4: Crear `ikctl/runner/utils.py` con `resolve_remote_dir(kit, options) → str`
- [x] T5: Añadir `--remote-dir` flag en `main.py` y pasarlo a `RunOptions`
- [x] T6: Modificar `RemoteRunner._run_on_host()` para usar `resolve_remote_dir()`
- [x] T7: Modificar `DryRunRunner.run()` para usar `resolve_remote_dir()`
- [x] T8: Crear `tests/test_remote_dir.py`:
  - `test_default_remote_dir`: sin remote_dir → `.ikctl/<kit.name>/`
  - `test_remote_dir_from_yaml`: `kit.remote_dir` seteado → usa ese valor
  - `test_remote_dir_from_cli`: `options.remote_dir` seteado → usa CLI, ignora YAML
  - `test_remote_dir_cli_overrides_yaml`: ambos seteados → gana CLI
  - `test_dry_run_uses_resolved_remote_dir`: dry-run muestra el remote_dir correcto
- [x] T9: Ejecutar `./init.sh` — debe terminar con `[OK] Entorno listo`
