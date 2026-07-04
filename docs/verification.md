# Verificación — Cómo demostrar que el trabajo funciona

> Regla de oro: **el agente no dice "funciona", lo demuestra**.
> Toda feature termina con evidencia ejecutable.

## Niveles de verificación

### Nivel 1 — Tests unitarios (obligatorio)

Toda función pública en `ikctl/` tiene al menos un test en `tests/` que cubre:

1. El camino feliz.
2. Al menos un camino de error si la función puede fallar.

Comando:

```bash
uv run pytest tests -v
```

### Nivel 2 — Código que toca SSH/SFTP (obligatorio)

Se mockea siempre con `unittest.mock`. Nunca conexiones SSH reales en tests:

```python
import pytest
from unittest.mock import MagicMock, patch
from ikctl.connection.options import SSHOptions
from ikctl.connection.ssh import SSHConnection

@pytest.fixture
def mock_ssh_client():
    with patch("paramiko.SSHClient") as mock_cls:
        client = MagicMock()
        mock_cls.return_value = client
        client.get_transport.return_value = MagicMock()
        yield client

def test_connect_with_key(mock_ssh_client):
    opts = SSHOptions(hostname="10.0.0.1", username="ubuntu", key_filename="/path/key")
    conn = SSHConnection(opts)
    mock_ssh_client.connect.assert_called_once()
```

Para tests de `RemoteRunner`, mockear la `connection_factory`:

```python
from unittest.mock import MagicMock
from ikctl.runner.remote import RemoteRunner
from ikctl.config.models import KitPipeline, ServerGroup

def test_run_uploads_files():
    conn = MagicMock()
    conn.open_sftp.return_value = MagicMock()
    conn.exec_command.return_value = ("output\n", "", 0)

    kit = KitPipeline(uploads=["/local/script.sh"], pipeline=["/local/script.sh"])
    servers = ServerGroup(user="ubuntu", port=22, hosts=["10.0.0.1"])

    runner = RemoteRunner(connection_factory=lambda host: conn)

    with patch("ikctl.runner.remote.SftpTransfer") as MockSftp:
        MockSftp.return_value.list_dir.return_value = []
        results = runner.run(kit, servers, object())

    assert results[0].success is True
```

### Nivel 3 — Configuración (obligatorio para features de config)

Usar `tempfile.TemporaryDirectory` con YAMLs reales:

```python
import os, tempfile, yaml, pytest

@pytest.fixture
def config_dir():
    with tempfile.TemporaryDirectory() as tmp:
        config = {
            "context": "local",
            "contexts": {
                "local": {
                    "path_kits": tmp,
                    "path_servers": tmp,
                    "path_secrets": "",
                    "mode": "local",
                    "timeout_connect": 30.0,
                    "timeout_exec": 120.0,
                }
            }
        }
        with open(os.path.join(tmp, "config"), "w") as f:
            yaml.dump(config, f)
        yield tmp
```

### Nivel 4 — Entorno completo (antes de declarar done)

```bash
./init.sh
```

Debe terminar con `[OK] Entorno listo`. Si no, la feature no está done.

## Anti-patrones (no hacer)

- ❌ "He añadido el comando, debería funcionar." → falta test ejecutable.
- ❌ Test que solo verifica que no lanza excepción. → comprobar el resultado concreto.
- ❌ Conexión SSH real en tests. → usar `unittest.mock` + `patch("paramiko.SSHClient")`.
- ❌ Mockear `sys.exit` para esconder un fallo. → corregir el fallo.
- ❌ Declarar done sin `./init.sh` verde.
