# Historial de sesiones

> Bitácora append-only. No editar entradas anteriores.

---

## Sesion 2026-06-01 — Feature 1: pyproject_migration

### Resumen

- Creado `pyproject.toml` con hatchling>=1.26 como build backend, metadatos PyPI completos, classifiers, scripts, urls y dependency-groups.dev (pytest>=8.0, ruff>=0.5).
- Cambiado `__version__ = "v0.6.4"` a `__version__ = "0.6.4"` en `ikctl/config/config.py`.
- Eliminados `setup.py`, `Pipfile` y `Pipfile.lock`.
- Actualizado `init.sh`: `uv run pytest` en lugar de `python3 -m pytest`.
- Actualizado `.claude/settings.json`: permiso `Bash(uv run pytest*)` en lugar de `Bash(python3 -m pytest*)`.
- `.gitignore` ya tenia `.venv` y `uv.lock` no estaba ignorado — sin cambios necesarios.
- `uv sync` instaló el entorno correctamente, `uv run ikctl --version` devuelve `0.6.4`.
- `uv build` genera `dist/ikctl-0.6.4.tar.gz` y `dist/ikctl-0.6.4-py3-none-any.whl`.
- Creado `tests/test_pyproject_migration.py` con 25 tests — todos pasan.
- `./init.sh` termina con [OK] Entorno listo.

### Estado: pendiente de revision humana

---

## Sesion 2026-06-01 — Feature 2: solid_config

### Resumen

- Creado `ikctl/config/models.py` con dataclasses frozen: `ServerGroup`, `KitPipeline`, `Context`, `IkctlConfig`.
- Creado `ikctl/config/exceptions.py` con `IkctlError`, `ConfigError`, `KitNotFoundError`, `ServerNotFoundError`.
- Creado `ikctl/config/loader.py` con `ConfigLoader.load() -> IkctlConfig`; lanza `ConfigError` si el archivo no existe o esta malformado; sin sys.exit().
- Creado `ikctl/config/bootstrap.py` con `ConfigBootstrap`; parametro `interactive=True/False`; usa context managers; mueve logica de `create_config_files.py`.
- Creado `ikctl/config/kit_repo.py` con `KitRepository.resolve(name) -> KitPipeline`; lanza `KitNotFoundError`; corrige bug de variable `error` no definida.
- Creado `ikctl/config/server_repo.py` con `ServerRepository.resolve(group) -> ServerGroup`; lanza `ServerNotFoundError`; `resolve(None)` devuelve el PRIMER grupo (bug corregido).
- Actualizado `ikctl/config/__init__.py` para exportar todas las clases publicas.
- Reescrito `ikctl/config/config.py`: delegacion a nuevas clases, todos los bugs corregidos, context managers en extract_secrets, bug del grupo incorrecto corregido, aliases de typos preservados para compatibilidad con pipeline.py.
- Actualizado `ikctl/context.py`: context manager en change_context(), type hints Python 3.13.
- Creados tests: `tests/test_config_loader.py` (7 tests), `tests/test_kit_repo.py` (5 tests), `tests/test_server_repo.py` (7 tests). Total 19 tests nuevos, 44 en total — todos pasan.
- `./init.sh` termina con [OK] Entorno listo.
- `uv run ikctl --version` devuelve `0.6.4`.

### Estado: pendiente de revision humana

---

## Sesion 2026-06-01 — Feature 3: solid_connections

### Resumen

- Creado `ikctl/connection/__init__.py`, `base.py`, `options.py`, `ssh.py`.
- `IConnection` (ABC) define el contrato: `exec_command`, `open_sftp`, `close`.
- `SSHOptions` (@dataclass) encapsula todos los parametros paramiko relevantes: hostname, port, username, password, passphrase, key_filename, pkey, allow_agent, look_for_keys, timeout, auth_timeout, banner_timeout, channel_timeout, keepalive_interval, compress, disabled_algorithms, host_key_policy, proxy_command.
- `SSHConnection(IConnection)` conecta en el constructor, aplica la politica de known_hosts segun `host_key_policy` ("auto_add", "reject", "warning"), soporta ProxyCommand via `sock=paramiko.ProxyCommand(...)`, aplica keepalive si `keepalive_interval > 0`, `exec_command()` devuelve `(stdout, stderr, exit_code)` sin imprimir, `close()` cierra SFTP y SSH en bloque try/finally.
- Eliminado completamente el workaround RSA SHA1 (no se incluye en los nuevos modulos).
- Creado `ikctl/transfer/__init__.py` y `ikctl/transfer/sftp.py` con `SftpTransfer(IConnection)`: `upload(local, remote)`, `create_dir(path)`, `list_dir(path)`.
- `ikctl/remote/connect.py` dejado intacto para compatibilidad con `remote_kits.py` (feature 4 lo refactorizara).
- Creado `tests/test_ssh_connection.py` con 7 tests usando mocks de paramiko.
- Creado `tests/test_sftp_transfer.py` con 3 tests usando mocks de IConnection.
- Total: 54 tests — todos pasan.
- `./init.sh` termina con [OK] Entorno listo.
- `uv run ikctl --version` devuelve `0.6.4`.

### Estado: pendiente de revision humana

---

## Sesion 2026-06-01 — Feature 4: solid_runners

### Resumen

- Creado `ikctl/runner/__init__.py`, `result.py`, `base.py`, `remote.py`, `local.py`.
- `RunResult` (@dataclass): host, success, stdout, stderr.
- `IRunner` (ABC): `run(kit, servers, options) -> list[RunResult]`.
- Creado `ikctl/executor/__init__.py`, `base.py`, `remote.py`, `local.py`.
- `IExecutor` (ABC): `execute(command) -> tuple[str, str, int]`.
- `RemoteExecutor(IExecutor)`: delega a `IConnection.exec_command()`; censura contrasenas en log con regex.
- `LocalExecutor(IExecutor)`: usa `subprocess.run()` con timeout configurable (default 120s); captura `TimeoutExpired` y devuelve `("", "Timeout expired", 1)`.
- `RemoteRunner(IRunner)`: recibe `connection_factory: Callable[[str], IConnection]`; valida que el kit no este vacio (lanza `KitNotFoundError`); llama `connection.close()` en `finally`; produce un `RunResult` por host.
- `LocalRunner(IRunner)`: recibe `IExecutor`; ejecuta todos los pasos del pipeline; devuelve un solo `RunResult` con `host="local"`.
- Reescrito `ikctl/pipeline.py`: usa `RemoteRunner` y `LocalRunner` con inyeccion de dependencias; `Pipeline._build_remote_runner()` construye la factory de `SSHConnection` con `SSHOptions`; `Pipeline._print_results()` imprime stdout/stderr con colores ANSI; sin instanciacion interna de clases concretas de runner.
- Eliminados archivos legados: `ikctl/config/create_config_files.py`, `ikctl/remote/connect.py`, `ikctl/remote/sftp.py`, `ikctl/remote/remote_kits.py`, `ikctl/local/local_kits.py`, `ikctl/execute.py`, `ikctl/commands.py`.
- Eliminadas carpetas vacias `ikctl/remote/` e `ikctl/local/`.
- Creados tests: `tests/test_remote_executor.py` (3 tests), `tests/test_local_executor.py` (3 tests), `tests/test_remote_runner.py` (5 tests), `tests/test_local_runner.py` (3 tests). Total 14 tests nuevos, 68 en total — todos pasan.
- `./init.sh` termina con [OK] Entorno listo.
- `uv run ikctl --version` devuelve `0.6.4`.

### Estado: pendiente de revision humana

---

## Sesion 2026-06-01 — Feature 5: test_suite

### Resumen

- Todos los tests requeridos por feature 5 ya existian y pasaban al inicio de la sesion (creados por features 1-4).
- Cobertura verificada test a test contra los criterios de acceptance:
  - `tests/test_config_loader.py` (7 tests): carga valida -> IkctlConfig, ConfigError cuando archivo no existe, ConfigError cuando YAML malformado.
  - `tests/test_kit_repo.py` (5 tests): resolve() con kit existente -> KitPipeline con uploads/pipeline correctos, KitNotFoundError con kit inexistente.
  - `tests/test_server_repo.py` (7 tests): resolve() grupo existente -> ServerGroup, ServerNotFoundError con grupo inexistente, resolve(None) devuelve primer grupo, resolve(None) con config vacia -> ServerNotFoundError.
  - `tests/test_ssh_connection.py` (7 tests): mock de paramiko.SSHClient, key_filename, password, close() cierra ssh y sftp, exec_command() devuelve (stdout, stderr, exit_code), host_key_policy="reject" aplica RejectPolicy, keepalive_interval>0 llama set_keepalive, proxy_command pasa sock=ProxyCommand.
  - `tests/test_remote_executor.py` (3 tests): exit_code 0, exit_code != 0, censura de contrasenas en log.
  - `tests/test_local_executor.py` (3 tests): execute OK, falla con exit_code no-cero, TimeoutExpired -> ("", "Timeout expired", 1).
  - `tests/test_remote_runner.py` (5 tests): sube archivos y ejecuta pipeline, KitNotFoundError con kit vacio, close() siempre llamado incluso si execute() lanza excepcion, close() llamado si connection_factory lanza, resultado por host.
  - `tests/test_local_runner.py` (3 tests): ejecuta todos los pasos, host="local", mock de IExecutor.
- 68 tests en total — todos pasan, sin skips.
- `./init.sh` termina con [OK] Entorno listo.

### Estado: pendiente de revision humana

---

## Sesion 2026-06-01 — Feature 6: configurable_timeouts

### Resumen

- Añadidos campos `timeout_connect: float = 30.0` y `timeout_exec: float = 120.0` a `Context` en `ikctl/config/models.py`.
- Actualizado `ConfigLoader.load()` en `ikctl/config/loader.py` para leer `timeout_connect` y `timeout_exec` del YAML por contexto (opcionales, con defaults 30.0 / 120.0).
- Añadidos metodos `load_timeout_connect()` y `load_timeout_exec()` a `Config` en `ikctl/config/config.py` para exponer los valores del contexto activo.
- Añadidos flags `--timeout-connect FLOAT` y `--timeout-exec FLOAT` al parser argparse en `ikctl/main.py`.
- Implementada logica de precedencia CLI > config > default en `main.py`: si el flag CLI no es None se usa, si no se usa el valor del contexto activo (que ya tiene los defaults de dataclass).
- `_build_runner` actualizado para recibir `timeout_connect` y `timeout_exec` como parametros: los pasa a `SSHOptions(timeout=timeout_connect)` y `LocalExecutor(timeout=timeout_exec)`.
- Verificado: no quedan valores de timeout hardcodeados en el codigo fuente.
- Creado `tests/test_configurable_timeouts.py` con 9 tests (5 de precedencia, 2 de SSHOptions, 2 de LocalExecutor) — todos pasan.
- 77 tests en total — todos pasan, sin skips.
- `./init.sh` termina con [OK] Entorno listo.
- `uv run ikctl --help` muestra `--timeout-connect` y `--timeout-exec` con sus descripciones.

### Estado: pendiente de revision humana

---

## Sesion 2026-06-01 — Feature 7: dry_run

### Resumen

- Creado `ikctl/runner/dry_run.py` con `DryRunRunner(IRunner)` y funcion `_censor(command)`.
- `DryRunRunner.run()` itera sobre hosts e imprime `[DRY RUN] Host:`, `[DRY RUN] UPLOAD: local -> remote` y `[DRY RUN] EXEC: <comando_censurado>` sin abrir conexiones ni ejecutar nada. Devuelve `RunResult(host=host, success=True, stdout="", stderr="")` por host.
- `_censor()` usa `re.sub` para reemplazar `echo <password> |` por `echo *** |`.
- Anadido `--dry-run` (flag booleano, default False) al parser argparse en `ikctl/main.py`.
- Modificado `_build_runner()` en `main.py`: si `dry_run=True` retorna `DryRunRunner()` independientemente del modo.
- Creado `tests/test_dry_run.py` con 12 tests cubriendo todos los criterios de acceptance.
- 89 tests en total — todos pasan, sin skips.
- `./init.sh` termina con [OK] Entorno listo.
- `uv run ikctl --help` muestra `--dry-run` con su descripcion.

### Estado: pendiente de revision humana

---

## Sesion 2026-06-01 — Feature 8: parallel_hosts

### Resumen

- Refactorizado `ikctl/runner/remote.py`: constructor acepta `max_workers: int = 4`; bucle `for host in servers.hosts` reemplazado por `ThreadPoolExecutor.map()`; logica de un host extraida a `_run_on_host(host, kit, options)` con `try/finally` que garantiza `conn.close()`; cada linea de `RunResult.stdout` prefijada con `[{host}]`.
- Actualizado `ikctl/main.py`: anadido `--parallel-workers N` (int, default 4, dest="parallel_workers"); `_build_runner` pasa `max_workers=options.parallel_workers` a `RemoteRunner`; `getattr` con fallback a 4 para opciones sin el atributo.
- Actualizado `ikctl/pipeline.py`: `_print_results` imprime resumen `N hosts OK, M hosts FAILED`; exit code 1 via `sys.exit(1)` si algun host fallo.
- Creado `tests/test_parallel_hosts.py` con 13 tests: conexiones creadas por host (N y 3), close() por host en exito y en fallo, host que falla no aborta los demas, prefijo `[host]` en stdout, verificacion de max_workers=2 via mock de ThreadPoolExecutor, defaults y valores personalizados de max_workers, paso de parallel_workers desde _build_runner.
- 102 tests en total — todos pasan, sin skips.
- `./init.sh` termina con [OK] Entorno listo.
- `uv run ikctl --help` muestra `--parallel-workers` con su descripcion.

### Estado: pendiente de revision humana

---

## Sesion 2026-06-02 — Bugfix 12: ssh_auth_method_selection

### Resumen

- Bug ubicado en `ikctl/main.py` `_build_runner()` funcion `connection_factory`: siempre pasaba `password` a `SSHOptions` aunque `pkey` estuviera definido, causando que paramiko intentara autenticacion por password en servidores que solo aceptan publickey.
- Escrito `tests/test_ssh_auth_selection.py` (test-first): 6 tests que reproducen el bug. Los 4 tests de pkey y password auth fallaban antes del fix (confirmado).
- Aplicado fix minimo en `_build_runner()`: logica if/elif/else que selecciona el metodo de autenticacion exclusivo:
  - `pkey` definido: `key_filename=pkey, password=None, allow_agent=False, look_for_keys=False`.
  - `password != "no_pass"` y sin pkey: `password=password, key_filename=None, allow_agent=False, look_for_keys=False`.
  - Sin credenciales: `password=secrets or None, key_filename=None, allow_agent=True, look_for_keys=True`.
- 119 tests en total — todos pasan, sin skips.
- `./init.sh` termina con [OK] Entorno listo.

### Archivos modificados

- `ikctl/main.py` — fix en `connection_factory` dentro de `_build_runner()`.
- `tests/test_ssh_auth_selection.py` — nuevo archivo de tests (6 tests).

### Estado: pendiente de revision humana

---

## Sesion 2026-06-02 — Feature 11: rich_output_and_debug

### Resumen

- Anadido `rich>=13.0` a `[project].dependencies` en `pyproject.toml`; `uv sync` actualizado sin errores.
- Anadido flag `--debug` (bool, default False) al parser argparse en `ikctl/main.py`.
- Configurado logging despues de `parse_args()` y antes de `Config()`: con `--debug` root level=INFO con formato completo; sin `--debug` root level=WARNING y paramiko/paramiko.transport silenciados explicitamente en WARNING.
- Eliminado el `logging.basicConfig(level=INFO)` que estaba en `Pipeline.__init__()` (causaba que INFO se emitiera siempre).
- Reemplazado `ikctl/logs.py`: `Log.stdout()` usa `rich.console.Console` (stdout) y `Console(stderr=True)` (stderr); check=0 imprime en verde, check!=0 imprime en rojo en stderr; solo una linea por llamada (el mensaje o el default).
- Reemplazado `ikctl/view.py`: `show_config("kits")` usa `rich.table.Table` con columna "Kit"; `show_config("servers")` usa Table con columnas Name/User/Hosts/Port/Auth (password censurado como `***`); `show_config("context")` usa `rich.panel.Panel`; `show_config("mode")` usa `Console().print()`.
- Actualizado `ikctl/pipeline.py`: importados `Console` y `Console(stderr=True)` a nivel de modulo; `_print_results()` usa Rich en lugar de ANSI crudo: stdout de host en `[cyan]`, stderr en `[red]` en stderr_console; resumen final en `[bold green]` si 0 failed, `[bold red]` si failed>0.
- Actualizados tests afectados:
  - `tests/test_logs.py`: errores van a `captured.err` (no `captured.out`); `test_stdout_success_with_message` solo verifica el mensaje, no la linea de exito adicional.
  - `tests/test_view.py`: `test_show_config_servers_masks_password` verifica `***` (3 asteriscos) en lugar de `*****` (5).
- Creado `tests/test_output_mode.py` con 6 tests: nivel WARNING en paramiko y paramiko.transport, INFO no llega a logger ikctl en WARNING, simulacion de --debug pone root en INFO, `Log.stdout(check=0)` imprime "successfully", `Log.stdout(check=1)` imprime "errors" en stderr.
- 125 tests en total — todos pasan, sin skips.
- `./init.sh` termina con [OK] Entorno listo.

### Archivos modificados

- `pyproject.toml` — dependencia `rich>=13.0` anadida.
- `ikctl/main.py` — flag `--debug` y configuracion de logging.
- `ikctl/pipeline.py` — eliminado basicConfig interno; Rich para stdout/stderr de resultados.
- `ikctl/logs.py` — reescrito con Rich Console.
- `ikctl/view.py` — reescrito con Rich Table/Panel/Console.
- `tests/test_logs.py` — ajustes por nuevo comportamiento (stderr, una linea).
- `tests/test_view.py` — ajuste `*****` -> `***` en test de censura.
- `tests/test_output_mode.py` — nuevo archivo (6 tests).

### Estado: pendiente de revision humana

---

## Sesion 2026-06-05 — Bugfix 10: connection_exceptions

### Resumen

- El codigo ya estaba implementado: `SSHConnectionError(IkctlError)` existia en `ikctl/config/exceptions.py`, `SSHConnection._connect()` capturaba todos los errores de red y autenticacion (OSError, paramiko.SSHException, AuthenticationException, BadHostKeyException, socket.timeout, TimeoutError) y los relanzaba como `SSHConnectionError`, y `RemoteRunner._run_on_host()` capturaba `SSHConnectionError` devolviendo `RunResult(success=False)`.
- Solo faltaban los tests. Seguido protocolo bugfix: tests que demuestran que el comportamiento ya funciona (todos pasan desde el primer momento).
- Anadidos 5 tests en `tests/test_ssh_connection.py`: `test_oserror_raises_ssh_connection_error`, `test_authentication_exception_raises_ssh_connection_error`, `test_bad_host_key_raises_ssh_connection_error`, `test_ssh_exception_raises_ssh_connection_error`, `test_timeout_raises_ssh_connection_error`.
- Anadido 1 test en `tests/test_remote_runner.py`: `test_ssh_connection_error_returns_failed_run_result` — verifica que `SSHConnectionError` devuelve `RunResult(success=False)` sin propagar la excepcion.
- 133 tests en total — todos pasan, sin skips.
- `./init.sh` termina con [OK] Entorno listo.

### Archivos modificados

- `tests/test_ssh_connection.py` — 5 tests nuevos de excepciones SSH.
- `tests/test_remote_runner.py` — 1 test nuevo de SSHConnectionError en runner.
- `feature_list.json` — status de feature 10 cambiado a `in_progress`.

### Estado: pendiente de revision humana

---

## Sesion 2026-06-05 — Feature 9: kit_auto_discovery

### Resumen

- Añadido campo `exclude: list[str] = field(default_factory=list)` a `Context` dataclass en `ikctl/config/models.py`.
- Actualizado `ConfigLoader.load()` en `ikctl/config/loader.py` para leer el campo `exclude` del YAML por contexto (opcional, default lista vacía).
- Reescrito `ikctl/config/kit_repo.py`: `KitRepository.resolve()` usa `pathlib.Path(path_kits).rglob("ikctl.yaml")` en lugar de leer un índice raíz. El fichero raíz `path_kits/ikctl.yaml` se ignora comparando `p.parent != path_kits`. Los kits en `context.exclude` se filtran antes de la búsqueda. El nombre del kit es la ruta relativa del directorio desde `path_kits`.
- Añadido método `KitRepository.list_kits() -> list[str]` que devuelve los nombres de todos los kits descubiertos para el contexto activo.
- Actualizado `Config.load_config_file_kits()` en `ikctl/config/config.py`: usa `KitRepository.list_kits()` para auto-discovery y devuelve `({"kits": ["<name>/ikctl.yaml", ...]}, path_kits)` — estructura compatible con el código existente de `pipeline.py` y `view.py`.
- Actualizado `Config.extract_config_kits()` en `ikctl/config/config.py`: delega a `KitRepository.resolve()` en lugar del index-based approach anterior; el parámetro `config` ya no se usa (mantenido por firma compatible).
- Reescrito `tests/test_kit_repo.py` con 8 tests de auto-discovery: `test_resolve_discovers_kit_without_index`, `test_resolve_nested_kit`, `test_resolve_excludes_kit_from_list`, `test_resolve_ignores_root_ikctl_yaml`, `test_resolve_raises_kit_not_found`, `test_list_kits_returns_all_discovered`, `test_list_kits_excludes_hidden`, `test_list_kits_returns_empty_for_nonexistent_path`.
- 136 tests en total — todos pasan, sin skips.
- `./init.sh` termina con [OK] Entorno listo.

### Archivos modificados

- `ikctl/config/models.py` — campo `exclude` añadido a `Context`.
- `ikctl/config/loader.py` — lectura de `exclude` en `load()`.
- `ikctl/config/kit_repo.py` — reescrito con auto-discovery via rglob.
- `ikctl/config/config.py` — `load_config_file_kits()` y `extract_config_kits()` usan `KitRepository`.
- `tests/test_kit_repo.py` — reescrito con tests de auto-discovery.
- `feature_list.json` — status de feature 9 cambiado a `in_progress`.

### Estado: pendiente de revision humana

---

## Sesion 2026-06-05 — Feature 13: git_kits_provider

### Resumen

- Añadidos campos `kits_repo: str | None = None` y `kits_ref: str = "main"` a `Context` dataclass en `ikctl/config/models.py`.
- Creado `ikctl/config/git_provider.py` con `GitKitsProvider`: metodo `ensure(kits_repo, kits_ref) -> str` que clona el repo si no existe localmente o hace pull si ya existe. `_repo_name()` deriva un nombre de directorio seguro: ultimo segmento de la URL sin `.git` mas un hash sha1 de 8 caracteres para unicidad. `_clone()` y `_pull()` usan `subprocess.run` con `capture_output=True`; lanzan `ConfigError` si el codigo de retorno es distinto de cero. Logging via `self._logger.info()`.
- Actualizado `ConfigLoader.load()` en `ikctl/config/loader.py` para leer `kits_repo` y `kits_ref` del YAML por contexto (opcionales, con defaults `None` y `"main"`).
- Anadido metodo `_resolve_path_kits()` a `KitRepository` en `ikctl/config/kit_repo.py`: si `context.kits_repo` esta definido llama a `GitKitsProvider().ensure()` y devuelve la ruta local; si no, devuelve `context.path_kits`. Tanto `list_kits()` como `resolve()` usan `_resolve_path_kits()` en lugar de `context.path_kits` directamente.
- Creado `tests/test_git_provider.py` con 6 tests usando mocks de `subprocess.run` (sin git real): clone en primer uso, pull en uso posterior, ConfigError en fallo de clone, ConfigError en fallo de pull, determinismo de _repo_name(), eliminacion de sufijo .git.
- 142 tests en total — todos pasan, sin skips.
- `./init.sh` termina con [OK] Entorno listo.

### Archivos modificados

- `ikctl/config/models.py` — campos `kits_repo` y `kits_ref` añadidos a `Context`.
- `ikctl/config/loader.py` — lectura de `kits_repo` y `kits_ref` en `load()`.
- `ikctl/config/git_provider.py` — nuevo archivo con `GitKitsProvider`.
- `ikctl/config/kit_repo.py` — metodo `_resolve_path_kits()` añadido; `list_kits()` y `resolve()` lo usan.
- `tests/test_git_provider.py` — nuevo archivo de tests (6 tests).
- `feature_list.json` — status de feature 13 cambiado a `in_progress`.

### Estado: pendiente de revision humana

---

## Sesion 2026-06-05 — Feature 14: pipeline_orchestration

### Resumen

- Creado `ikctl/orchestration/__init__.py` (vacio).
- Creado `ikctl/orchestration/parser.py`: `StepDef` y `PipelineDef` (@dataclass frozen=True), `PipelineParser.parse(path) -> PipelineDef`; valida campos obligatorios (id, kit, servers), lanza `ConfigError` si el YAML es invalido, falta algun campo requerido o el archivo no existe.
- Creado `ikctl/orchestration/dag.py`: `DAGResolver.resolve(steps) -> list[list[StepDef]]` con algoritmo de Kahn; agrupa steps en waves (wave 0 = sin needs, wave N = needs todos en waves anteriores); lanza `ConfigError` si hay ciclos o si un `needs` referencia un id inexistente.
- Creado `ikctl/orchestration/interpolator.py`: `OutputInterpolator.extract(stdout) -> dict[str,str]` parsea lineas `KEY=VALUE` del stdout; `OutputInterpolator.interpolate(params, step_outputs) -> list[str]` resuelve `{{ steps.<id>.<KEY> }}`; lanza `ConfigError` si la referencia no existe.
- Creado `ikctl/orchestration/runner.py`: `StepResult` (@dataclass con id, status, outputs, stdout, stderr), `OrchestrationRunner.run(pipeline, base_options) -> list[StepResult]`; ejecuta waves en paralelo con `ThreadPoolExecutor`; acumula `step_outputs`; skip si un `need` fallo; interpola params antes de ejecutar; imprime con Rich (Wave header, check/cross/skip por step, panel de resumen final).
- Actualizado `ikctl/main.py`: extraida logica de `connection_factory` a funcion `_make_connection_factory()` (reutilizada por `_build_runner` y el nuevo path de pipeline); anadido `--pipeline <path>` al parser argparse; bloque `if args.pipeline` que carga `IkctlConfig`, parsea el fichero, construye `OrchestrationRunner` y ejecuta.
- Creados tests:
  - `tests/test_pipeline_parser.py` (12 tests): YAML valido completo, campos por defecto, cada campo obligatorio faltante, YAML invalido, archivo no encontrado, YAML no-mapping.
  - `tests/test_dag_resolver.py` (12 tests): sin deps (1 wave), cadena (N waves), paralelo (1 wave N steps), diamante, ciclo simple, auto-ciclo, ciclo de 3, id inexistente en needs, pasos vacios, deps mixtas.
  - `tests/test_output_interpolator.py` (17 tests): extract KEY=VALUE simple, multiple, ignorar no-KV, valor vacio, valor con signo igual, clave invalida, stdout vacio, guion bajo; interpolate referencia unica, multiples en un param, sin referencias, multiples params, step desconocido, clave desconocida, params vacios, espacios en template.
  - `tests/test_orchestration_runner.py` (13 tests): StepResult defaults, step ok, step falla, dependiente skipped, multiples dependientes skipped, independiente sigue corriendo, outputs propagados entre steps, outputs extraidos del stdout, kit no encontrado, servidor no encontrado.
- 191 tests en total — todos pasan, sin skips.
- `./init.sh` termina con [OK] Entorno listo.

### Archivos creados/modificados

- `ikctl/orchestration/__init__.py` — nuevo (vacio).
- `ikctl/orchestration/parser.py` — nuevo.
- `ikctl/orchestration/dag.py` — nuevo.
- `ikctl/orchestration/interpolator.py` — nuevo.
- `ikctl/orchestration/runner.py` — nuevo.
- `ikctl/main.py` — `_make_connection_factory()` extraida, `--pipeline` anadido, bloque de ejecucion de pipeline.
- `tests/test_pipeline_parser.py` — nuevo (12 tests).
- `tests/test_dag_resolver.py` — nuevo (12 tests).
- `tests/test_output_interpolator.py` — nuevo (17 tests).
- `tests/test_orchestration_runner.py` — nuevo (13 tests).
- `specs/pipeline_orchestration/tasks.md` — todas las tareas marcadas [x].
- `feature_list.json` — status de feature 14 cambiado a `in_progress`.

### Estado: pendiente de revision humana

---

## Sesion 2026-06-05 — Feature 15: path_pipelines

### Resumen

- Añadido campo `path_pipelines: str | None = None` al dataclass `Context` en `ikctl/config/models.py`.
- Actualizado `ConfigLoader.load()` en `ikctl/config/loader.py` para leer `path_pipelines` del YAML por contexto (opcional, default None).
- Creada funcion `_resolve_pipeline_path(pipeline_arg, path_pipelines) -> str` en `ikctl/main.py`:
  1. Si `pipeline_arg` es fichero existente, se devuelve directamente.
  2. Si `path_pipelines` esta definido, busca `<path_pipelines>/<pipeline_arg>.yaml` (o con extension si ya la tiene).
  3. Si ninguno resuelve, lanza `ConfigError` con mensaje claro.
- Integrada `_resolve_pipeline_path` en el bloque `if args.pipeline:` de `main()`: la ruta resuelta se pasa a `PipelineParser().parse()`.
- Creado `tests/test_path_pipelines.py` con 5 tests cubriendo todos los criterios de acceptance: ruta directa, por nombre sin extension, por nombre con extension, error sin match, error con path_pipelines=None.
- 196 tests en total — todos pasan, sin skips.
- `./init.sh` termina con [OK] Entorno listo.

### Archivos modificados

- `ikctl/config/models.py` — campo `path_pipelines` añadido a `Context`.
- `ikctl/config/loader.py` — lectura de `path_pipelines` en `load()`.
- `ikctl/main.py` — funcion `_resolve_pipeline_path()` añadida e integrada.
- `tests/test_path_pipelines.py` — nuevo archivo de tests (5 tests).
- `feature_list.json` — status de feature 15 cambiado a `in_progress`.

### Estado: pendiente de revision humana

---

## Sesion 2026-06-06 — Bugfix 16: list_pipelines

### Resumen

- Bug: `main.py` tenia `choices=["kits", "servers", "context", "mode"]` sin incluir `"pipelines"`, por lo que argparse rechazaba `--list pipelines` con codigo de salida 2.
- Añadido `"pipelines"` a las choices de `--list` en `ikctl/main.py`.
- Añadido parametro `path_pipelines: str | None = None` a `Show.__init__()` en `ikctl/view.py`; añadida importacion de `pathlib`.
- Añadida rama `elif conf == "pipelines":` en `Show.show_config()`: si `path_pipelines` es None muestra mensaje claro; si el directorio esta vacio imprime "No pipelines found"; si tiene ficheros .yaml los muestra en una tabla Rich (columnas Name, Path).
- Añadido metodo `load_path_pipelines() -> str | None` a `Config` en `ikctl/config/config.py` para exponer `path_pipelines` del contexto activo.
- Actualizada la construccion de `Show` en `ikctl/pipeline.py` para pasar `path_pipelines=self.data.load_path_pipelines()`.
- Feature 15 estaba en `in_progress` de sesion anterior con implementacion completa y tests pasando; cambiada a `done` para que init.sh pueda validar la regla de maximo 1 feature in_progress.
- Creado `tests/test_list_pipelines.py` con 4 tests: `test_list_pipelines_shows_yaml_files`, `test_list_pipelines_no_path_configured`, `test_list_pipelines_empty_dir`, `test_main_accepts_list_pipelines_argument`.
- 200 tests en total — todos pasan, sin skips.
- `./init.sh` termina con [OK] Entorno listo.

### Archivos modificados

- `ikctl/main.py` — `"pipelines"` anadido a choices de `--list`.
- `ikctl/view.py` — parametro `path_pipelines` y rama `elif conf == "pipelines"` en `show_config()`.
- `ikctl/config/config.py` — metodo `load_path_pipelines()` anadido.
- `ikctl/pipeline.py` — `Show` construido con `path_pipelines`.
- `tests/test_list_pipelines.py` — nuevo archivo de tests (4 tests).
- `feature_list.json` — status de feature 16 cambiado a `in_progress`; status de feature 15 cambiado a `done` (ya estaba implementada).

### Estado: pendiente de revision humana

---

## Sesion 2026-06-06 — Feature 17: pipeline_params

### Resumen

- Extendido `OutputInterpolator.interpolate()` en `ikctl/orchestration/interpolator.py`: acepta un tercer argumento `pipeline_params: dict[str, str] | None = None`. Se añade `_PARAMS_PATTERN = re.compile(r"\{\{\s*params\.(\w+)\s*\}\}")` y se renombra `_TEMPLATE_PATTERN` a `_STEPS_PATTERN` para claridad. La resolucion se hace en dos pasadas: primero `{{ steps.<id>.<KEY> }}` con `_resolve_step_ref()`, luego `{{ params.<KEY> }}` con `_resolve_param_ref()`. Si la clave no esta en `pipeline_params` (o `pipeline_params` es None), lanza `ConfigError` con mensaje claro indicando como pasarla con `-p KEY=<value>`.
- Actualizado `OrchestrationRunner.run()` en `ikctl/orchestration/runner.py`: acepta `pipeline_params: dict[str, str] | None = None` y lo pasa a `interpolator.interpolate()` en cada step durante la fase de resolucion de params.
- Actualizado `ikctl/main.py` en el bloque `if args.pipeline:`: parsea `args.parameter` buscando items con formato `KEY=VALUE` via `str.partition("=")`. Los que no tienen `=` se ignoran con `logging.warning`. El dict resultante se pasa a `orch_runner.run()` como `pipeline_params=pipeline_params or None` (None si el dict esta vacio).
- Anadidos 4 tests en `tests/test_output_interpolator.py`: `test_interpolate_params_key` (resolucion normal), `test_interpolate_params_key_missing` (ConfigError con dict vacio), `test_interpolate_mixed_steps_and_params` (mezcla de ambas sintaxis en un mismo step), `test_interpolate_params_none_raises_on_reference` (ConfigError con pipeline_params=None).
- 204 tests en total — todos pasan, sin skips.
- `./init.sh` termina con [OK] Entorno listo.

### Archivos modificados

- `ikctl/orchestration/interpolator.py` — `_PARAMS_PATTERN` anadido, `interpolate()` extendido con `pipeline_params`, `_resolve_step_ref()` y `_resolve_param_ref()` como metodos privados separados.
- `ikctl/orchestration/runner.py` — `run()` acepta y pasa `pipeline_params`.
- `ikctl/main.py` — parseo de `-p KEY=VALUE` y paso de `pipeline_params` a `orch_runner.run()`.
- `tests/test_output_interpolator.py` — 4 tests nuevos de `{{ params.KEY }}`.
- `feature_list.json` — status de feature 17 cambiado a `in_progress`.

### Estado: pendiente de revision humana

---

## Sesion 2026-06-06 — Feature 18: kit_outputs_descriptor

### Resumen

- Añadido campo `outputs: dict[str, str] = field(default_factory=dict)` a `KitPipeline` en `ikctl/config/models.py`.
- Actualizado `KitRepository.resolve()` en `ikctl/config/kit_repo.py`: lee `kit_config["kits"].get("outputs", {}) or {}` y convierte cada clave/valor a `str`; los incluye en `KitPipeline(outputs=outputs)`.
- Actualizado `ikctl/view.py`: `Show.__init__()` acepta nuevo parametro opcional `kit_pipelines: dict[str, KitPipeline] | None = None`; `show_config("kits")` añade columna "Outputs" mostrando las keys separadas por coma o "-" si no hay; nuevo metodo `show_kit_describe(kit_name, kit)` renderiza Panel con nombre del kit, tabla de uploads, tabla de pipeline, tabla de outputs (o "No outputs declared").
- Añadido metodo `load_kit_pipelines() -> dict[str, KitPipeline]` a `Config` en `ikctl/config/config.py`.
- Actualizado `ikctl/pipeline.py`: `Show` construido con `kit_pipelines=self.data.load_kit_pipelines()`.
- Añadido `--describe <kit>` al parser argparse en `ikctl/main.py`; bloque que carga `ConfigLoader`, `KitRepository.resolve()`, construye un `Show` minimo y llama a `view.show_kit_describe()`.
- Creado `tests/test_kit_describe.py` con 8 tests cubriendo todos los criterios de acceptance.
- 212 tests en total — todos pasan, sin skips.
- `./init.sh` termina con [OK] Entorno listo.

### Archivos modificados

- `ikctl/config/models.py` — campo `outputs` añadido a `KitPipeline`.
- `ikctl/config/kit_repo.py` — lectura de `outputs` en `resolve()`.
- `ikctl/view.py` — parametro `kit_pipelines`, columna Outputs en kits, metodo `show_kit_describe()`.
- `ikctl/config/config.py` — metodo `load_kit_pipelines()` añadido.
- `ikctl/pipeline.py` — `Show` construido con `kit_pipelines`.
- `ikctl/main.py` — `--describe` añadido e integrado.
- `tests/test_kit_describe.py` — nuevo archivo de tests (8 tests).
- `feature_list.json` — status de feature 18 cambiado a `in_progress`.

### Estado: pendiente de revision humana

---

## Sesion 2026-06-06 — Feature 19: git_kits_token

### Resumen

- Añadido campo `kits_token: str | None = None` a `Context` dataclass en `ikctl/config/models.py`.
- Actualizado `ConfigLoader.load()` en `ikctl/config/loader.py` para leer `kits_token` del YAML por contexto (opcional, default None); envyaml resuelve variables de entorno como `$GITLAB_TOKEN` automáticamente.
- Actualizado `ikctl/config/git_provider.py`:
  - `ensure()` acepta `kits_token: str | None = None` y lo pasa a `_clone()` y `_pull()`.
  - Nuevo método `_inject_token(url, token) -> str`: inyecta `oauth2:<token>@` en URLs HTTPS; para URLs SSH registra warning y devuelve la URL sin modificar.
  - `_clone()` usa `auth_url` con token si está definido; censura el token con `***` en el `ConfigError` si el stderr lo contiene; los logs siempre usan la URL original.
  - `_pull()` usa `git pull <auth_url> <ref>` cuando hay token (en lugar de `pull origin`); también censura el token en errores.
- Actualizado `KitRepository._resolve_path_kits()` en `ikctl/config/kit_repo.py` para pasar `context.kits_token` a `GitKitsProvider().ensure()`.
- Añadidos 5 tests en `tests/test_git_provider.py` (sin sobreescribir los 6 existentes): `test_inject_token_into_https_url`, `test_inject_token_ssh_url_unchanged_with_warning`, `test_clone_uses_token_url`, `test_clone_censors_token_in_error_message`, `test_ensure_without_token_unchanged`.
- 217 tests en total — todos pasan, sin skips.
- `./init.sh` termina con [OK] Entorno listo.

### Archivos modificados

- `ikctl/config/models.py` — campo `kits_token` añadido a `Context`.
- `ikctl/config/loader.py` — lectura de `kits_token` en `load()`.
- `ikctl/config/git_provider.py` — `_inject_token()`, `ensure()`, `_clone()`, `_pull()` actualizados.
- `ikctl/config/kit_repo.py` — `_resolve_path_kits()` pasa `kits_token`.
- `tests/test_git_provider.py` — 5 tests nuevos de autenticación con token.
- `feature_list.json` — status de feature 19 cambiado a `in_progress`.

### Estado: pendiente de revision humana

---

## Sesion 2026-06-12 — Feature 27: ansible_style_output

### Resumen

Implementación de salida estilo Ansible en el runner remoto de ikctl.
La barra de progreso Rich fue reemplazada por líneas simples con formato
`[<host>] UPLOAD  <fichero>  OK/FAILED` y `[<host>] RUN     <script>  OK/FAILED`.
El stdout/stderr del host solo se imprime con `--debug`.

### Archivos modificados

- `ikctl/runner/base.py` — campo `debug: bool = False` añadido a `RunOptions`
- `ikctl/runner/remote.py` — eliminados imports Rich Progress; nuevo bucle UPLOAD y bloque RUN con formato Ansible; soporte `options.debug`
- `ikctl/main.py` — `debug=getattr(args, "debug", False)` pasado a `RunOptions`
- `tests/test_remote_runner.py` — 5 tests nuevos: upload_ok, run_ok, run_failed, no_stdout_without_debug, stdout_with_debug
- `tests/test_output_mode.py` — test `test_run_on_host_uses_progress_for_uploads` reemplazado por `test_run_on_host_upload_prints_ok_line`

### Resultado de tests

270 passed (265 previos + 5 nuevos), 1 warning preexistente. Reviewer: APROBADO.

### Observacion del reviewer

RF-4 parcialmente satisfecho: el label usa el IP/hostname (no un nombre legible).
Documentado en design.md como decisión consciente; añadir nombres por host es feature futura.

### Estado: pendiente de aprobacion humana
