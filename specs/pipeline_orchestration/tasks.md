# Implementation tasks — pipeline_orchestration

> Ordered list. Complete each task before starting the next.
> Update [ ] to [x] as you go. Document blockers in progress/current.md.

- [x] T1: Crear `ikctl/orchestration/__init__.py`
- [x] T2: Crear `ikctl/orchestration/parser.py` con `StepDef`, `PipelineDef` y `PipelineParser.parse()`; lanza `ConfigError` si el YAML es inválido o faltan campos obligatorios
- [x] T3: Crear `ikctl/orchestration/dag.py` con `DAGResolver.resolve()` usando Kahn's algorithm; lanza `ConfigError` si hay ciclos; devuelve `list[list[StepDef]]` (waves)
- [x] T4: Crear `ikctl/orchestration/interpolator.py` con `OutputInterpolator.extract()` y `OutputInterpolator.interpolate()`; lanza `ConfigError` si una referencia `{{ steps.<id>.<KEY> }}` no existe
- [x] T5: Crear `ikctl/orchestration/runner.py` con `StepResult` y `OrchestrationRunner.run()` que ejecuta el DAG por waves usando `ThreadPoolExecutor`
- [x] T6: Integrar `OrchestrationRunner` con `RemoteRunner`/`LocalRunner` para ejecutar cada step como un kit normal
- [x] T7: Implementar lógica de skip: si un step de la wave anterior falló, los dependientes se marcan como SKIPPED sin ejecutar
- [x] T8: Implementar interpolación de params entre steps: extraer outputs del step anterior e interpolar antes de ejecutar el siguiente
- [x] T9: Añadir `--pipeline <fichero.yaml>` a `main.py` como alternativa a `--install`
- [x] T10: Añadir salida Rich para el pipeline: waves, estado por step (✓/✗/⊘), resumen final en panel
- [x] T11: Escribir tests:
  - `tests/test_pipeline_parser.py`: YAML válido, campos obligatorios faltantes, YAML malformado
  - `tests/test_dag_resolver.py`: sin dependencias (1 wave), dependencias en cadena, paralelo, ciclo detectado
  - `tests/test_output_interpolator.py`: extract KEY=VALUE, interpolate {{ }}, referencia inexistente
  - `tests/test_orchestration_runner.py`: ejecución en orden, skip si falla dependencia, outputs pasados entre steps
- [x] T12: Ejecutar `./init.sh` — debe terminar con `[OK] Entorno listo`
