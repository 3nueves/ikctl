"""OrchestrationRunner: executes a pipeline DAG using existing kit runners."""
from __future__ import annotations

import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from ikctl.config.exceptions import ConfigError, KitNotFoundError, ServerNotFoundError
from ikctl.config.kit_repo import KitRepository
from ikctl.config.models import IkctlConfig
from ikctl.config.server_repo import ServerRepository
from ikctl.executor.local import LocalExecutor
from ikctl.orchestration.dag import DAGResolver
from ikctl.orchestration.interpolator import OutputInterpolator
from ikctl.orchestration.parser import PipelineDef, StepDef
from ikctl.runner.local import LocalRunner
from ikctl.runner.remote import RemoteRunner


@dataclass
class StepResult:
    """Result of executing a single pipeline step."""

    id: str
    status: str   # "ok" | "failed" | "skipped"
    outputs: dict[str, str] = field(default_factory=dict)
    stdout: str = ""
    stderr: str = ""


class OrchestrationRunner:
    """Executes a PipelineDef DAG wave by wave using RemoteRunner or LocalRunner."""

    def __init__(
        self,
        config: IkctlConfig,
        connection_factory: object,
        max_workers: int = 4,
        mode: str = "remote",
        timeout_exec: float = 120.0,
    ) -> None:
        """Initialise with resolved config and connection details."""
        self._config = config
        self._connection_factory = connection_factory
        self._max_workers = max_workers
        self._mode = mode
        self._timeout_exec = timeout_exec
        self._logger = logging.getLogger(__name__)

    def run(
        self,
        pipeline: PipelineDef,
        base_options: object,
        pipeline_params: dict[str, str] | None = None,
    ) -> list[StepResult]:
        """Execute the DAG. Returns one StepResult per step.

        Steps are grouped into waves and each wave is run in parallel with
        ThreadPoolExecutor. Outputs are extracted and passed to downstream steps.
        pipeline_params are passed from the CLI via -p KEY=VALUE and resolved
        as {{ params.KEY }} in step param strings.
        """
        dag = DAGResolver()
        waves = dag.resolve(pipeline.steps)
        interpolator = OutputInterpolator()

        step_outputs: dict[str, dict[str, str]] = {}
        failed_ids: set[str] = set()
        all_results: list[StepResult] = []

        for wave in waves:
            # Determine which steps to skip in this wave
            to_execute: list[StepDef] = []
            for step in wave:
                if any(dep in failed_ids for dep in step.needs):
                    result = StepResult(id=step.id, status="skipped")
                    all_results.append(result)
                    failed_ids.add(step.id)
                else:
                    to_execute.append(step)

            if not to_execute:
                continue

            # Execute remaining steps in parallel
            futures = {}
            with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
                for step in to_execute:
                    try:
                        resolved_params = interpolator.interpolate(
                            step.params, step_outputs, pipeline_params
                        )
                    except ConfigError as exc:
                        self._logger.error("Interpolation error for step '%s': %s", step.id, exc)
                        result = StepResult(id=step.id, status="failed", stderr=str(exc))
                        all_results.append(result)
                        failed_ids.add(step.id)
                        continue

                    future = pool.submit(self._execute_step, step, resolved_params, base_options)
                    futures[future] = step

                for future in as_completed(futures):
                    step = futures[future]
                    try:
                        result = future.result()
                    except Exception as exc:
                        self._logger.error("Unexpected error in step '%s': %s", step.id, exc)
                        result = StepResult(id=step.id, status="failed", stderr=str(exc))

                    all_results.append(result)

                    if result.status == "ok":
                        step_outputs[step.id] = result.outputs
                    else:
                        failed_ids.add(step.id)

        return all_results

    def _execute_step(self, step: StepDef, resolved_params: list[str], base_options: object) -> StepResult:
        """Execute a single step using the appropriate runner. Returns a StepResult."""
        self._logger.info("Executing step '%s' (kit=%s, servers=%s)", step.id, step.kit, step.servers)

        try:
            kit = KitRepository(self._config).resolve(step.kit)
        except KitNotFoundError as exc:
            return StepResult(id=step.id, status="failed", stderr=str(exc))

        try:
            servers = ServerRepository(self._config).resolve(step.servers)
        except ServerNotFoundError as exc:
            return StepResult(id=step.id, status="failed", stderr=str(exc))

        # Build step-specific options namespace
        step_options = argparse.Namespace(
            sudo="sudo" if step.sudo else None,
            parameter=resolved_params if resolved_params else None,
            mode=self._mode,
            dry_run=getattr(base_options, "dry_run", False),
            parallel_workers=self._max_workers,
        )

        if self._mode == "local":
            executor = LocalExecutor(timeout=self._timeout_exec)
            runner = LocalRunner(executor)
        else:
            runner = RemoteRunner(self._connection_factory, max_workers=self._max_workers)

        try:
            run_results = runner.run(kit, servers, step_options)
        except Exception as exc:
            self._logger.error("Runner error in step '%s': %s", step.id, exc)
            return StepResult(id=step.id, status="failed", stderr=str(exc))

        combined_stdout = "\n".join(r.stdout for r in run_results if r.stdout)
        combined_stderr = "\n".join(r.stderr for r in run_results if r.stderr)
        success = all(r.success for r in run_results)

        outputs = OutputInterpolator().extract(combined_stdout)

        return StepResult(
            id=step.id,
            status="ok" if success else "failed",
            outputs=outputs,
            stdout=combined_stdout,
            stderr=combined_stderr,
        )
