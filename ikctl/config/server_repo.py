"""Resolves server group configurations from the loaded ikctl config."""
from __future__ import annotations

import logging

from envyaml import EnvYAML

from ikctl.exceptions import ServerNotFoundError
from ikctl.config.models import IkctlConfig, ServerGroup


class ServerRepository:
    """Resolves server groups from the servers config file."""

    def __init__(self, config: IkctlConfig) -> None:
        self._config = config
        self._logger = logging.getLogger(__name__)

    def resolve(self, group: str | None = None) -> ServerGroup:
        """Returns the ServerGroup for the given group name.

        When group is None, returns the first group available.
        Raises ServerNotFoundError if the group does not exist or no groups are defined.
        """
        context = self._config.contexts[self._config.context]
        servers_path = context.path_servers

        try:
            servers_config = EnvYAML(servers_path + "/config.yaml", strict=False)
        except Exception as exc:
            raise ServerNotFoundError(
                f"Could not load servers config at '{servers_path}/config.yaml': {exc}"
            ) from exc

        servers: list = servers_config.get("servers", [])
        if not servers:
            raise ServerNotFoundError(
                f"No servers defined in '{servers_path}/config.yaml'"
            )

        for entry in servers:
            name = entry.get("name")
            if group is None or group == name:
                hosts = entry.get("hosts", [])
                if not hosts:
                    self._logger.warning("Server group '%s' has no hosts", name)
                server_group = ServerGroup(
                    user=entry.get("user", "root"),
                    port=int(entry.get("port", 22)),
                    hosts=list(hosts),
                    password=entry.get("password") or None,
                    pkey=entry.get("pkey", None),
                )
                self._logger.debug("Resolved server group '%s'", name)
                return server_group

        raise ServerNotFoundError(f"Server group '{group}' not found in '{servers_path}/config.yaml'")
