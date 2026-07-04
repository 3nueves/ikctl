"""Parser for pipeline YAML files."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import yaml

from ikctl.exceptions import ConfigError


@dataclass(frozen=True)
class StepDef:
    """Represents a single step in an orchestration pipeline."""

    id: str
    kit: str
    servers: str
    sudo: bool = False
    params: list[str] = field(default_factory=list)
    needs: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PipelineDef:
    """Represents a complete pipeline definition with its steps."""

    name: str
    steps: list[StepDef]


class PipelineParser:
    """Reads and validates a pipeline YAML file."""

    def __init__(self) -> None:
        """Initialize the parser."""
        self._logger = logging.getLogger(__name__)

    def parse(self, path: str) -> PipelineDef:
        """Read the YAML file and return a PipelineDef. Raises ConfigError if invalid."""
        try:
            with open(path, encoding="utf-8") as f:
                raw = yaml.safe_load(f)
        except FileNotFoundError:
            raise ConfigError(f"Pipeline file not found: {path}")
        except yaml.YAMLError as exc:
            raise ConfigError(f"Invalid YAML in pipeline file '{path}': {exc}")

        if not isinstance(raw, dict):
            raise ConfigError(f"Pipeline file '{path}' must be a YAML mapping")

        if "name" not in raw:
            raise ConfigError(f"Pipeline file '{path}' missing required field: name")

        if "steps" not in raw or not isinstance(raw["steps"], list):
            raise ConfigError(f"Pipeline file '{path}' missing required field: steps")

        steps: list[StepDef] = []
        for i, step_raw in enumerate(raw["steps"]):
            if not isinstance(step_raw, dict):
                raise ConfigError(f"Step {i} in pipeline '{path}' is not a mapping")

            for required in ("id", "kit", "servers"):
                if required not in step_raw:
                    raise ConfigError(
                        f"Step {i} in pipeline '{path}' missing required field: {required}"
                    )

            steps.append(StepDef(
                id=str(step_raw["id"]),
                kit=str(step_raw["kit"]),
                servers=str(step_raw["servers"]),
                sudo=bool(step_raw.get("sudo", False)),
                params=list(step_raw.get("params", [])),
                needs=list(step_raw.get("needs", [])),
            ))

        self._logger.info("Parsed pipeline '%s' with %d steps", raw["name"], len(steps))
        return PipelineDef(name=str(raw["name"]), steps=steps)
