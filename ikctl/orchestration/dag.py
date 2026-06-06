"""DAG resolver for pipeline step dependencies."""
from __future__ import annotations

import logging
from collections import deque

from ikctl.config.exceptions import ConfigError
from ikctl.orchestration.parser import StepDef


class DAGResolver:
    """Resolves pipeline step dependencies into ordered execution waves."""

    def __init__(self) -> None:
        """Initialize the DAG resolver."""
        self._logger = logging.getLogger(__name__)

    def resolve(self, steps: list[StepDef]) -> list[list[StepDef]]:
        """Return steps grouped into waves using Kahn's algorithm.

        Wave 0 contains steps with no needs.
        Wave N contains steps whose needs are all resolved in earlier waves.
        Raises ConfigError on cycles or missing step ids in needs.
        """
        step_by_id: dict[str, StepDef] = {s.id: s for s in steps}

        # Validate all needs references exist
        for step in steps:
            for dep_id in step.needs:
                if dep_id not in step_by_id:
                    raise ConfigError(
                        f"Step '{step.id}' has unknown dependency '{dep_id}'"
                    )

        # Build in-degree map and adjacency list (dep -> dependents)
        in_degree: dict[str, int] = {s.id: 0 for s in steps}
        dependents: dict[str, list[str]] = {s.id: [] for s in steps}

        for step in steps:
            in_degree[step.id] = len(step.needs)
            for dep_id in step.needs:
                dependents[dep_id].append(step.id)

        # Assign wave numbers using BFS (Kahn's)
        wave_number: dict[str, int] = {}
        queue: deque[str] = deque()

        for step_id, degree in in_degree.items():
            if degree == 0:
                queue.append(step_id)
                wave_number[step_id] = 0

        processed_count = 0

        while queue:
            step_id = queue.popleft()
            processed_count += 1
            current_wave = wave_number[step_id]

            for dep_id in dependents[step_id]:
                in_degree[dep_id] -= 1
                # The wave of a step is max(wave of all its needs) + 1
                new_wave = current_wave + 1
                if dep_id not in wave_number or wave_number[dep_id] < new_wave:
                    wave_number[dep_id] = new_wave
                if in_degree[dep_id] == 0:
                    queue.append(dep_id)

        if processed_count != len(steps):
            raise ConfigError("Pipeline contains a dependency cycle")

        # Group steps by wave number
        max_wave = max(wave_number.values(), default=-1)
        waves: list[list[StepDef]] = [[] for _ in range(max_wave + 1)]
        for step in steps:
            waves[wave_number[step.id]].append(step)

        self._logger.info("Resolved %d steps into %d waves", len(steps), len(waves))
        return waves
