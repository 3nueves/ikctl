# Design — cli_defined_server

## Changes to `ikctl/main.py`

### 1. New argparse arguments

```python
parser.add_argument("--host", action="append", default=None, dest="host",
    help="Remote host (repeatable). When used, --user/--password/--port/--key replace servers/config.yaml")
parser.add_argument("--user", default="root",
    help="SSH user (default: root, only with --host)")
parser.add_argument("--password", default=None,
    help="SSH password (only with --host)")
parser.add_argument("--port", type=int, default=22,
    help="SSH port (default: 22, only with --host)")
parser.add_argument("--key", default=None,
    help="Path to SSH private key (only with --host)")
```

### 2. Conditional server resolution

```
if args.host:
    servers = ServerGroup(user=args.user, port=args.port, hosts=args.host,
                          password=args.password or None, pkey=args.key or None)
    secrets = None
    config_mode = "remote"
    timeout_connect = args.timeout_connect or 30.0
    timeout_exec = args.timeout_exec or 120.0
    sudo_password = args.sudo_password or args.password or None
else:
    # existing YAML-based path unchanged
```

### 3. sudo_password resolution with --host

```
sudo_password = args.sudo_password or args.password or None
```

## Files to modify

- `ikctl/main.py`: new args + conditional server loading
- `tests/test_cli_defined_server.py`: new test file

## Files not modified

- `ikctl/connection/`: unchanged — ServerGroup → SSHOptions → SSHConnection works identically
- `ikctl/runner/`: unchanged — RemoteRunner, LocalRunner, DryRunRunner accept ServerGroup regardless of origin
- `ikctl/config/`: unchanged — YAML-based server loading only used when --host is absent