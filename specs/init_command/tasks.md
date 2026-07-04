# Implementation tasks — init_command

> Ordered list. Complete each task before starting the next.
> Update [ ] to [x] as you go. Document blockers in progress/current.md.

- [ ] T1: Crear `ikctl/init/__init__.py` (vacío)
- [ ] T2: Crear `ikctl/init/wizard.py` con `InitPaths`, `_write_if_absent()` e `InitWizard.__init__()` aceptando `base`, `auto`, `force`
- [ ] T3: Implementar `InitWizard._step()`: imprime número de paso, título y descripción con Rich; en modo interactivo pide confirmación; llama a `create_fn()`
- [ ] T4: Implementar `InitWizard._create_config()`: genera `~/.ikctl/config` con contexto `demo` usando `_write_if_absent()`
- [ ] T5: Implementar `InitWizard._create_servers()`: genera `~/.ikctl/servers/config.yaml` con grupo `demo-servers`
- [ ] T6: Implementar `InitWizard._create_kit()`: genera `~/kits/show-date/ikctl.yaml` y `~/kits/show-date/date.sh`
- [ ] T7: Implementar `InitWizard._create_pipeline()`: genera `~/.ikctl/pipelines/example.yaml`
- [ ] T8: Implementar `InitWizard._print_summary()`: panel Rich con archivos creados y comandos sugeridos
- [ ] T9: Implementar `InitWizard.run()`: llama a los 4 `_step()` en orden y llama a `_print_summary()`
- [ ] T10: Añadir `--init`, `--auto` y `--force` al parser en `main.py`; añadir `args.init` al check de argumentos accionables (feature 22)
- [ ] T11: Integrar `InitWizard` en `main.py`: si `args.init`, construir wizard y llamar a `.run()` antes de cargar config
- [ ] T12: Escribir `tests/test_init_command.py` cubriendo:
  - `--auto` crea los 5 archivos esperados en `tmp_path`
  - Idempotencia: segunda ejecución no sobrescribe archivos existentes
  - `--force` sobrescribe archivos existentes
  - Estructura de archivos creada es correcta (contenido mínimo verificado)
  - `ikctl --init` está en el check de argumentos accionables (no muestra help)
- [ ] T13: Ejecutar `uv run pytest tests/ -v` — todos los tests en verde
- [ ] T14: Ejecutar `./init.sh` — debe terminar con `[OK] Entorno listo`
