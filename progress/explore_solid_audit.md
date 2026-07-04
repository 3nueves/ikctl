# Auditoría SOLID — ikctl/

**Fecha:** 2026-06-12  
**Alcance:** todos los `.py` bajo `ikctl/` (excluidos 8 `__init__.py` sin lógica de negocio)  
**Módulos analizados:** 30  
**Con violaciones:** 12  
**Sin violaciones:** 18  

---

## 1. Módulos que SÍ siguen SOLID

| # | Módulo | Clases / elementos principales |
|---|--------|-------------------------------|
| 1 | `logs.py` | `Log` |
| 2 | `config/models.py` | `ServerGroup`, `KitPipeline`, `Context`, `IkctlConfig` |
| 3 | `config/exceptions.py` | `IkctlError`, `ConfigError`, `KitNotFoundError`, `ServerNotFoundError`, `SSHConnectionError`, `RunnerError` |
| 4 | `config/loader.py` | `ConfigLoader` |
| 5 | `config/server_repo.py` | `ServerRepository` |
| 6 | `config/git_provider.py` | `GitKitsProvider` |
| 7 | `connection/ssh.py` | `SSHConnection` |
| 8 | `connection/options.py` | `SSHOptions` |
| 9 | `executor/base.py` | `IExecutor` |
| 10 | `executor/local.py` | `LocalExecutor` |
| 11 | `executor/remote.py` | `RemoteExecutor` |
| 12 | `runner/base.py` | `IRunner`, `RunOptions`, `RunResult` |
| 13 | `runner/local.py` | `LocalRunner` |
| 14 | `runner/dry_run.py` | `DryRunRunner` |
| 15 | `transfer/sftp.py` | `SftpTransfer` |
| 16 | `orchestration/dag.py` | `DAGResolver` |
| 17 | `orchestration/parser.py` | `PipelineParser` |
| 18 | `init/scaffold.py` | `Scaffold`, `ScaffoldPaths`, `write_if_absent` |

---

## 2. Módulos que NO siguen SOLID

| # | Módulo | Principio(s) | Motivo (una línea) |
|---|--------|-------------|-------------------|
| 1 | `main.py` | **SRP · OCP · DIP** | `main()` mezcla parseo de args, carga de config, construcción de runner, orquestación de pipeline y renderizado de resultados; instancia directamente `Config`, `ConfigLoader`, `LocalExecutor`, `DryRunRunner`, `LocalRunner`, `RemoteRunner`; añadir un nuevo comando CLI requiere modificar la función. |
| 2 | `context.py` — `Context` | **SRP · DIP** | La clase combina lectura YAML del fichero, validación de contexto, escritura del fichero y llamadas a `sys.exit()` (lógica de dominio mezclada con CLI); instancia directamente `Config()` sin abstracción. |
| 3 | `pipeline.py` — `Pipeline` | **SRP · DIP** | El constructor carga la configuración, inicializa la vista, extrae servidores y dispara la ejecución (múltiples razones de cambio); instancia directamente `Config()`, `Context()`, `Log()` y `Show()`. |
| 4 | `view.py` — `Show` | **SRP · OCP** | `show_config()` gestiona cinco modos de visualización distintos (kits, servers, context, mode, pipelines) en un solo método con cadena if-elif; añadir un nuevo modo de listado requiere modificar el método. |
| 5 | `config/config.py` — `Config` | **SRP · OCP · DIP** | God class que agrupa bootstrap, carga de config, resolución de kits, resolución de servidores, secretos, timeouts y pipelines; cada nueva concern de configuración exige modificar la clase; instancia directamente `ConfigBootstrap`, `ConfigLoader` y `KitRepository`. |
| 6 | `config/bootstrap.py` — `ConfigBootstrap` | **SRP** | `_confirm()` mezcla interacción con el usuario (prompt en consola) con la lógica de setup del sistema de ficheros, generando dos razones de cambio independientes en la misma clase. |
| 7 | `config/kit_repo.py` — `KitRepository` | **DIP** | `_resolve_path_kits()` instancia directamente `GitKitsProvider()` sin inyección, acoplando el repositorio a una implementación concreta de proveedor git. |
| 8 | `connection/base.py` — `IConnection` | **ISP** | La interfaz agrupa `exec_command` (ejecución de comandos) y `open_sftp` (transferencia de ficheros) en un solo contrato, forzando a cualquier implementador a proveer ambas capacidades aunque solo necesite una. |
| 9 | `runner/remote.py` — `RemoteRunner` | **SRP · DIP** | `_run_on_host` mezcla lógica de ejecución con salida a consola (Rich printing de estado UPLOAD/RUN); instancia directamente `SftpTransfer` y `RemoteExecutor` dentro del método. |
| 10 | `orchestration/interpolator.py` — `OutputInterpolator` | **SRP** | La clase combina extracción de outputs de stdout (`extract`) con interpolación de templates (`interpolate`), dos concerns que pueden cambiar de forma independiente y podrían separarse. |
| 11 | `orchestration/runner.py` — `OrchestrationRunner` | **SRP · OCP · DIP** | `_execute_step` resuelve kits, servidores, selecciona runner e instancia `KitRepository`, `ServerRepository`, `LocalExecutor`, `LocalRunner`, `RemoteRunner`; añadir un nuevo modo de ejecución (p.ej. "docker") requiere modificar el método. |
| 12 | `init/wizard.py` — `InitWizard` | **SRP** | La clase mezcla interacción UI (`_ask_paths` con prompts a `input()`) con la orquestación del flujo de scaffold, lo que genera dos razones de cambio: lógica de UX y lógica de instalación. |

---

## 3. Resumen numérico

| Métrica | Valor |
|---------|-------|
| Módulos `.py` analizados (excl. `__init__.py`) | **30** |
| Módulos sin violaciones SOLID | **18** (60 %) |
| Módulos con al menos una violación | **12** (40 %) |
| Violaciones SRP | 8 módulos |
| Violaciones OCP | 4 módulos |
| Violaciones LSP | 0 módulos |
| Violaciones ISP | 1 módulo (`connection/base.py`) |
| Violaciones DIP | 7 módulos |

> **Nota LSP:** Ninguna subclase viola LSP — todas las implementaciones concretas
> (`SSHConnection`, `LocalExecutor`, `RemoteExecutor`, `LocalRunner`, `RemoteRunner`,
> `DryRunRunner`) son sustituibles por sus respectivas abstracciones sin alterar
> el comportamiento del sistema.

---

## 4. Hotspots prioritarios (múltiples violaciones)

1. **`config/config.py`** — SRP + OCP + DIP (God class, mayor deuda técnica del proyecto)
2. **`orchestration/runner.py`** — SRP + OCP + DIP (acoplamiento máximo en el runner de orquestación)
3. **`main.py`** — SRP + OCP + DIP (función de entrada que lo hace todo)
4. **`pipeline.py`** — SRP + DIP (constructor con efectos secundarios y dependencias concretas)
