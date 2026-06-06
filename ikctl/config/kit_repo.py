"""Resolves kit configurations from the loaded ikctl config."""
from __future__ import annotations

import logging
import pathlib

from envyaml import EnvYAML

from ikctl.config.exceptions import KitNotFoundError
from ikctl.config.models import IkctlConfig, KitPipeline


class KitRepository:
    """Resolves kit configurations from the loaded config using auto-discovery."""

    def __init__(self, config: IkctlConfig) -> None:
        self._config = config
        self._logger = logging.getLogger(__name__)

    def _resolve_path_kits(self) -> str:
        """Returns the effective path_kits, cloning/pulling from git if kits_repo is set."""
        context = self._config.contexts[self._config.context]
        if context.kits_repo:
            from ikctl.config.git_provider import GitKitsProvider
            return GitKitsProvider().ensure(context.kits_repo, context.kits_ref, context.kits_token)
        return context.path_kits

    def _discover_manifests(self, path_kits: pathlib.Path, exclude: list[str]) -> list[pathlib.Path]:
        """Returns ikctl.yaml manifests found under path_kits, skipping root and excluded kits."""
        return [
            p for p in path_kits.rglob("ikctl.yaml")
            if p.parent != path_kits
            and str(p.parent.relative_to(path_kits)) not in exclude
        ]

    def list_kits(self) -> list[str]:
        """Returns all discovered kit names for the active context."""
        context = self._config.contexts[self._config.context]
        path_kits = pathlib.Path(self._resolve_path_kits())

        if not path_kits.is_dir():
            return []

        manifests = self._discover_manifests(path_kits, context.exclude)
        return sorted(str(p.parent.relative_to(path_kits)) for p in manifests)

    def resolve(self, name: str) -> KitPipeline:
        """Returns the KitPipeline for the given kit name using auto-discovery.

        Raises KitNotFoundError if the kit does not exist or is excluded.
        """
        context = self._config.contexts[self._config.context]
        path_kits = pathlib.Path(self._resolve_path_kits())

        if not path_kits.is_dir():
            raise KitNotFoundError(f"Kit '{name}' not found: path_kits '{path_kits}' does not exist")

        manifests = self._discover_manifests(path_kits, context.exclude)

        for manifest in manifests:
            kit_name = str(manifest.parent.relative_to(path_kits))
            if kit_name == name:
                kit_dir = manifest.parent
                try:
                    kit_config = EnvYAML(str(manifest), strict=False)
                except Exception as exc:
                    raise KitNotFoundError(
                        f"Could not load kit manifest at '{manifest}': {exc}"
                    ) from exc

                uploads: list[str] = [
                    str(kit_dir / upload)
                    for upload in kit_config["kits"]["uploads"]
                ]
                pipeline: list[str] = [
                    str(kit_dir / step)
                    for step in kit_config["kits"]["pipeline"]
                ]

                raw_outputs = kit_config["kits"].get("outputs", {}) or {}
                outputs: dict[str, str] = {str(k): str(v) for k, v in raw_outputs.items()}

                self._logger.debug(
                    "Resolved kit '%s': %d uploads, %d pipeline steps, %d outputs",
                    name,
                    len(uploads),
                    len(pipeline),
                    len(outputs),
                )
                return KitPipeline(uploads=uploads, pipeline=pipeline, outputs=outputs)

        raise KitNotFoundError(f"Kit '{name}' not found under '{path_kits}'")
