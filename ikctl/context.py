"""Manages ikctl context switching."""
from __future__ import annotations

import logging
import pathlib
import sys

import yaml
from yaml.loader import SafeLoader

from ikctl.config.config import Config

_logger = logging.getLogger(__name__)


class Context:
    """Manages reading and switching ikctl contexts."""

    def __init__(self) -> None:
        self.conf = Config()
        self.init_context()

    def init_context(self) -> None:
        """Loads contexts from the config file."""
        self.config = yaml.load(
            pathlib.Path(self.conf.path_config_file).read_text(encoding="utf-8"),
            Loader=SafeLoader,
        )

    def check_context_exist(self, context: str) -> bool:
        """Returns True if the named context exists in config."""
        for ctx in self.config["contexts"]:
            if ctx == context:
                return True
        return False

    def change_context(self, context: str) -> None:
        """Writes the new active context to the config file."""
        if not self.check_context_exist(context):
            print("\n -- Context not exists --\n", file=sys.stderr)
            sys.exit(1)

        self.config["context"] = context
        config_file = yaml.dump(self.config, default_flow_style=False)

        with open(self.conf.path_config_file, "w", encoding="utf-8") as f:
            f.writelines(config_file)

        print(f'\n\n-- Context "{context}" changed succefully --\n\n')
