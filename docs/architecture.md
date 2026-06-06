# Arquitectura — Qué significa "hacer un buen trabajo" en ikctl

> Este documento describe la arquitectura **target**. Las features en
> `feature_list.json` acercan el código a este estado. El reviewer evalúa
> cada cambio contra este documento.

## Principios SOLID

| Principio | Cómo aplica en ikctl |
|-----------|----------------------|
| **S** — Single Responsibility | Cada clase tiene una sola razón para cambiar. `KitRepository` solo resuelve kits. `SSHConnection` solo gestiona la conexión. |
| **O** — Open/Closed | Añadir un nuevo tipo de runner (Docker, Ansible) no requiere modificar `Pipeline`. Solo implementar `IRunner`. |
| **L** — Liskov Substitution | `RemoteRunner` y `LocalRunner` son intercambiables donde se espere `IRunner`. |
| **I** — Interface Segregation | `IConnection` expone solo lo que un runner necesita: `exec_command`, `open_sftp`, `close`. |
| **D** — Dependency Inversion | `Pipeline` depende de `IRunner`, no de `RemoteRunner`. Las dependencias concretas se inyectan desde fuera. |

## Estructura de módulos (target)

```
ikctl/
├── main.py              # argparse — solo parsea y llama a Pipeline
├── pipeline.py          # Orquestador — depende de IRunner, no de clases concretas
├── view.py              # Listados (--list)
├── logs.py              # Colores ANSI para resultados finales
│
├── config/
│   ├── models.py        # @dataclass: ServerGroup, KitPipeline, Context, IkctlConfig
│   ├── exceptions.py    # ConfigError, KitNotFoundError, ServerNotFoundError
│   ├── loader.py        # ConfigLoader: carga ~/.ikctl/config → IkctlConfig
│   ├── bootstrap.py     # ConfigBootstrap: crea config inicial si no existe
│   ├── kit_repo.py      # KitRepository.resolve(name) → KitPipeline
│   └── server_repo.py   # ServerRepository.resolve(group) → ServerGroup
│
├── connection/
│   ├── base.py          # IConnection (ABC): exec_command, open_sftp, close
│   ├── options.py       # @dataclass SSHOptions: todos los parámetros paramiko
│   └── ssh.py           # SSHConnection(IConnection): implementación paramiko completa
│
├── transfer/
│   └── sftp.py          # SftpTransfer: upload(local_path, remote_path)
│
├── executor/
│   ├── base.py          # IExecutor (ABC): execute(cmd) → (stdout, stderr, exit_code)
│   ├── remote.py        # RemoteExecutor(IExecutor): via IConnection.exec_command()
│   └── local.py         # LocalExecutor(IExecutor): via subprocess.run()
│
└── runner/
    ├── base.py          # IRunner (ABC): run(kit, servers, options) → list[RunResult]
    ├── result.py        # @dataclass RunResult: host, success, stdout, stderr
    ├── remote.py        # RemoteRunner(IRunner): SftpTransfer + RemoteExecutor por host
    └── local.py         # LocalRunner(IRunner): LocalExecutor
```

## Flujo de datos (target)

```
usuario (args CLI)
    → main.py (argparse)
        → Pipeline(runner: IRunner, config: IkctlConfig)
            │
            ├─ --list     → View.show_config(...)
            │
            ├─ --install + remote
            │   → KitRepository.resolve(name)   → KitPipeline
            │   → ServerRepository.resolve(grp) → ServerGroup
            │   → RemoteRunner.run(kit, servers, opts)
            │       → por cada host:
            │           → SSHConnection(SSHOptions).open()
            │           → SftpTransfer.upload(local, remote) × N archivos
            │           → RemoteExecutor.execute(cmd) × N pasos
            │           → connection.close()       ← siempre, incluso si falla
            │       → list[RunResult]
            │
            └─ --install + local
                → KitRepository.resolve(name) → KitPipeline
                → LocalRunner.run(kit, ...)
                    → LocalExecutor.execute(cmd) × N pasos
                → list[RunResult]
```

## Reglas de diseño (no negociables)

1. **Las capas internas lanzan excepciones, no llaman a `sys.exit()`.** Solo
   `Pipeline` y `main.py` capturan excepciones del dominio y llaman a
   `sys.exit()` con un mensaje claro.

2. **Las capas internas no imprimen.** Los resultados se devuelven como
   `RunResult`. `Pipeline` decide qué mostrar usando `logs.py`.

3. **`close()` siempre se llama**, incluso si la ejecución falla. Usar
   `try/finally` o context manager en `RemoteRunner`.

4. **Toda escritura de archivo usa context manager** (`with open(...) as f`).

5. **Inyección de dependencias desde `Pipeline`.** `Pipeline` recibe las
   dependencias concretas como parámetros; no las instancia internamente.

6. **Dependencias externas acotadas.** Solo `paramiko>=3.0`, `pyaml`,
   `envyaml`. Nueva dependencia → estado `blocked` en `feature_list.json`.

7. **Secretos censurados en cualquier log o salida**. Nunca imprimir
   contraseñas. Usar `***` en comandos que incluyan credenciales.

## Qué NO hacer

- No instanciar `SSHConnection` directamente en `Pipeline`. Se inyecta.
- No leer archivos de config desde `runner/` ni `executor/`. Reciben todo como parámetros.
- No mezclar transferencia de archivos con ejecución de comandos.
- No añadir lógica de negocio en `main.py`.
- No usar `Optional[str]` ni `List[str]` de `typing`. Usar `str | None` y `list[str]`.
