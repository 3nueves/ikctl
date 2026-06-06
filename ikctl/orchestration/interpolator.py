"""Output interpolator for pipeline step parameters."""
from __future__ import annotations

import logging
import re

from ikctl.config.exceptions import ConfigError

_STEPS_PATTERN = re.compile(r"\{\{\s*steps\.([^.}]+)\.([^}]+?)\s*\}\}")
_PARAMS_PATTERN = re.compile(r"\{\{\s*params\.(\w+)\s*\}\}")
_KV_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


class OutputInterpolator:
    """Parses KEY=VALUE output from steps and interpolates template references."""

    def __init__(self) -> None:
        """Initialize the interpolator."""
        self._logger = logging.getLogger(__name__)

    def extract(self, stdout: str) -> dict[str, str]:
        """Extract KEY=VALUE pairs from stdout. Ignores lines that do not match."""
        outputs: dict[str, str] = {}
        for line in stdout.splitlines():
            match = _KV_PATTERN.match(line.strip())
            if match:
                key, value = match.group(1), match.group(2)
                outputs[key] = value
        return outputs

    def interpolate(
        self,
        params: list[str],
        step_outputs: dict[str, dict[str, str]],
        pipeline_params: dict[str, str] | None = None,
    ) -> list[str]:
        """Resolve {{ steps.<id>.<KEY> }} and {{ params.<KEY> }} references in each param string.

        - step_outputs: accumulated outputs from previous steps
        - pipeline_params: parameters passed from the CLI via -p KEY=VALUE
        Raises ConfigError if a referenced step id, step key, or param key does not exist.
        """
        resolved: list[str] = []
        for param in params:
            # First resolve {{ steps.<id>.<KEY> }} references
            result = _STEPS_PATTERN.sub(
                lambda m, _so=step_outputs, _p=param: self._resolve_step_ref(m, _so, _p),
                param,
            )
            # Then resolve {{ params.<KEY> }} references
            result = _PARAMS_PATTERN.sub(
                lambda m, _pp=pipeline_params, _p=param: self._resolve_param_ref(m, _pp, _p),
                result,
            )
            resolved.append(result)
        return resolved

    def _resolve_step_ref(
        self,
        match: re.Match,
        step_outputs: dict[str, dict[str, str]],
        original: str,
    ) -> str:
        """Resolve a single {{ steps.<id>.<KEY> }} reference. Raises ConfigError if not found."""
        step_id = match.group(1)
        key = match.group(2)

        if step_id not in step_outputs:
            raise ConfigError(
                f"Reference to unknown step '{step_id}' in param '{original}'"
            )
        if key not in step_outputs[step_id]:
            raise ConfigError(
                f"Step '{step_id}' has no output key '{key}' (param: '{original}')"
            )

        return step_outputs[step_id][key]

    def _resolve_param_ref(
        self,
        match: re.Match,
        pipeline_params: dict[str, str] | None,
        original: str,
    ) -> str:
        """Resolve a single {{ params.<KEY> }} reference. Raises ConfigError if not found."""
        key = match.group(1)

        if pipeline_params is None or key not in pipeline_params:
            raise ConfigError(
                f"Pipeline param '{key}' not defined. Pass it with -p {key}=<value>"
            )

        return pipeline_params[key]
