# CHECKPOINTS — Criterios de "done" para ikctl

> El reviewer marca [x] o [ ] en cada checkpoint antes de emitir veredicto.
> Un solo [ ] bloquea la aprobación.
> Los checkpoints marcados con (bugfix) o (refactor) solo aplican a ese tipo.

## Verificación del entorno

- [ ] C1: `./init.sh` termina con `[OK] Entorno listo`
- [ ] C2: Todos los tests nuevos pasan (`uv run pytest tests -v`)

## Calidad del código

- [ ] C3: Nombres siguen convenciones: `snake_case` para funciones/variables, `PascalCase` para clases
- [ ] C4: Logging via `self._logger` (obtenido con `logging.getLogger(__name__)`), no `print()` para mensajes internos
- [ ] C5: Errores al usuario: mensaje claro + `sys.exit()`, nunca un stack trace crudo

## Cobertura de tests

- [ ] C6: Todo código nuevo que toca SSH/SFTP usa mocks de `unittest.mock`, no conexiones reales
- [ ] C7: Cada función pública tiene al menos un test del camino feliz y uno de error
- [ ] C8: Tests son funciones `def test_*` o clases `class Test*` sin herencia de `unittest.TestCase`; fixtures de pytest para estado compartido

## Arquitectura

- [ ] C9: El cambio respeta las capas definidas en `docs/architecture.md`
- [ ] C10: No se añaden dependencias externas sin haberlo discutido (ver `pyproject.toml`)
- [ ] C11: Cada criterio de `acceptance` en `feature_list.json` se cumple y se puede demostrar

## Solo para bugfix

- [ ] C12: *(bugfix)* Existe un test que reproduce el bug y **fallaba antes del fix** — el fix lo hace pasar
- [ ] C13: *(bugfix)* El fix es mínimo: no introduce refactors ni features fuera del scope del bug

## Solo para refactor

- [ ] C14: *(refactor)* Todos los tests existentes antes del refactor siguen pasando sin modificación
- [ ] C15: *(refactor)* El comportamiento externo observable es idéntico al anterior (misma CLI, mismos outputs)
- [ ] C16: *(refactor)* No se añade funcionalidad nueva dentro del refactor (scope cerrado)
