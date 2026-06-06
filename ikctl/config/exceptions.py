"""Domain exceptions for ikctl."""
from __future__ import annotations


class IkctlError(Exception):
    """Base exception for all ikctl errors."""


class ConfigError(IkctlError):
    """Raised when configuration cannot be loaded or is malformed."""


class KitNotFoundError(IkctlError):
    """Raised when a requested kit does not exist."""


class ServerNotFoundError(IkctlError):
    """Raised when a requested server group does not exist."""


class SSHConnectionError(IkctlError):
    """Raised when an SSH connection cannot be established."""
