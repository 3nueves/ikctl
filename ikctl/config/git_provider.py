"""Clones or pulls a git repository and returns the local cache path."""
from __future__ import annotations

import hashlib
import logging
import pathlib
import subprocess

from ikctl.exceptions import ConfigError


class GitKitsProvider:
    """Clones or pulls a git repository and returns the local path."""

    CACHE_DIR = pathlib.Path.home() / ".ikctl" / "cache"

    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)

    def ensure(self, kits_repo: str, kits_ref: str = "main", kits_token: str | None = None) -> str:
        """Ensures the repo is cloned/updated locally.

        Returns the local path to the cloned repo as a string.
        Raises ConfigError if git fails.
        """
        repo_name = self._repo_name(kits_repo)
        local_path = self.CACHE_DIR / repo_name

        if not local_path.exists():
            self._clone(kits_repo, kits_ref, local_path, kits_token)
        else:
            self._pull(kits_ref, local_path, kits_repo, kits_token)

        return str(local_path)

    def _inject_token(self, url: str, token: str) -> str:
        """Inject token into HTTPS URL. Returns url unchanged if not HTTPS."""
        if url.startswith("https://"):
            without_scheme = url[len("https://"):]
            return f"https://oauth2:{token}@{without_scheme}"
        self._logger.warning(
            "kits_token is set but kits_repo uses SSH — token ignored. "
            "SSH authentication is handled by the SSH agent."
        )
        return url

    def _repo_name(self, kits_repo: str) -> str:
        """Derives a safe directory name from the repo URL."""
        name = kits_repo.rstrip("/").split("/")[-1].removesuffix(".git")
        short_hash = hashlib.sha1(kits_repo.encode()).hexdigest()[:8]
        return f"{name}-{short_hash}"

    def _clone(
        self,
        kits_repo: str,
        kits_ref: str,
        local_path: pathlib.Path,
        kits_token: str | None = None,
    ) -> None:
        """Clones the repository at the given ref into local_path."""
        local_path.parent.mkdir(parents=True, exist_ok=True)
        auth_url = self._inject_token(kits_repo, kits_token) if kits_token else kits_repo
        result = subprocess.run(
            ["git", "clone", auth_url, "--branch", kits_ref, "--depth", "1", str(local_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            safe_stderr = result.stderr.replace(kits_token, "***") if kits_token else result.stderr
            raise ConfigError(f"Failed to clone {kits_repo}: {safe_stderr.strip()}")
        self._logger.info("Cloned %s@%s to %s", kits_repo, kits_ref, local_path)

    def _pull(
        self,
        kits_ref: str,
        local_path: pathlib.Path,
        kits_repo: str = "",
        kits_token: str | None = None,
    ) -> None:
        """Pulls the latest changes for the given ref in local_path."""
        if kits_token and kits_repo:
            auth_url = self._inject_token(kits_repo, kits_token)
            cmd = ["git", "-C", str(local_path), "pull", auth_url, kits_ref]
        else:
            cmd = ["git", "-C", str(local_path), "pull", "origin", kits_ref]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            safe_stderr = result.stderr.replace(kits_token, "***") if kits_token else result.stderr
            raise ConfigError(f"Failed to pull {kits_ref} in {local_path}: {safe_stderr.strip()}")
        self._logger.info("Pulled %s in %s", kits_ref, local_path)
