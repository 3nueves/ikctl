"""Tests for GitKitsProvider."""
from __future__ import annotations

import pathlib
from unittest.mock import MagicMock, patch

import pytest

from ikctl.exceptions import ConfigError
from ikctl.config.git_provider import GitKitsProvider


def _make_completed_process(returncode: int = 0, stderr: str = "") -> MagicMock:
    """Builds a mock CompletedProcess with the given returncode and stderr."""
    mock = MagicMock()
    mock.returncode = returncode
    mock.stderr = stderr
    return mock


def test_ensure_clones_on_first_use(tmp_path: pathlib.Path) -> None:
    """When the local directory does not exist, ensure() calls git clone."""
    provider = GitKitsProvider()
    provider.CACHE_DIR = tmp_path  # type: ignore[misc]

    repo_url = "https://gitlab.com/company/kits.git"
    ref = "main"

    with patch("ikctl.config.git_provider.subprocess.run") as mock_run:
        mock_run.return_value = _make_completed_process(returncode=0)

        result = provider.ensure(repo_url, ref)

    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert call_args[0] == "git"
    assert "clone" in call_args
    assert repo_url in call_args
    assert ref in call_args
    assert result.startswith(str(tmp_path))


def test_ensure_pulls_on_subsequent_use(tmp_path: pathlib.Path) -> None:
    """When the local directory already exists, ensure() calls git pull."""
    provider = GitKitsProvider()
    provider.CACHE_DIR = tmp_path  # type: ignore[misc]

    repo_url = "https://gitlab.com/company/kits.git"
    ref = "main"

    repo_name = provider._repo_name(repo_url)
    local_path = tmp_path / repo_name
    local_path.mkdir(parents=True)

    with patch("ikctl.config.git_provider.subprocess.run") as mock_run:
        mock_run.return_value = _make_completed_process(returncode=0)

        result = provider.ensure(repo_url, ref)

    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert call_args[0] == "git"
    assert "pull" in call_args
    assert ref in call_args
    assert result == str(local_path)


def test_ensure_raises_config_error_on_clone_failure(tmp_path: pathlib.Path) -> None:
    """ensure() raises ConfigError when git clone returns a non-zero exit code."""
    provider = GitKitsProvider()
    provider.CACHE_DIR = tmp_path  # type: ignore[misc]

    repo_url = "https://gitlab.com/company/private-kits.git"

    with patch("ikctl.config.git_provider.subprocess.run") as mock_run:
        mock_run.return_value = _make_completed_process(
            returncode=1,
            stderr="Repository not found.",
        )

        with pytest.raises(ConfigError, match="Failed to clone"):
            provider.ensure(repo_url, "main")


def test_ensure_raises_config_error_on_pull_failure(tmp_path: pathlib.Path) -> None:
    """ensure() raises ConfigError when git pull returns a non-zero exit code."""
    provider = GitKitsProvider()
    provider.CACHE_DIR = tmp_path  # type: ignore[misc]

    repo_url = "https://gitlab.com/company/kits.git"
    ref = "feature-branch"

    repo_name = provider._repo_name(repo_url)
    local_path = tmp_path / repo_name
    local_path.mkdir(parents=True)

    with patch("ikctl.config.git_provider.subprocess.run") as mock_run:
        mock_run.return_value = _make_completed_process(
            returncode=1,
            stderr="error: pathspec 'feature-branch' did not match any file(s) known to git.",
        )

        with pytest.raises(ConfigError, match="Failed to pull"):
            provider.ensure(repo_url, ref)


def test_repo_name_is_deterministic() -> None:
    """_repo_name() returns the same value for the same URL on every call."""
    provider = GitKitsProvider()
    url = "https://gitlab.com/company/kits.git"

    name1 = provider._repo_name(url)
    name2 = provider._repo_name(url)

    assert name1 == name2


def test_repo_name_strips_git_suffix() -> None:
    """_repo_name() removes the .git suffix from the repo URL."""
    provider = GitKitsProvider()
    url = "https://gitlab.com/company/repo.git"

    name = provider._repo_name(url)

    assert name.startswith("repo-")
    assert ".git" not in name


def test_inject_token_into_https_url() -> None:
    """_inject_token() inserts oauth2:<token>@ into HTTPS URLs."""
    provider = GitKitsProvider()
    url = "https://gitlab.com/company/repo.git"
    token = "my_secret_token"

    result = provider._inject_token(url, token)

    assert result == f"https://oauth2:{token}@gitlab.com/company/repo.git"


def test_inject_token_ssh_url_unchanged_with_warning() -> None:
    """_inject_token() leaves SSH URLs unchanged and logs a warning."""
    provider = GitKitsProvider()
    url = "git@gitlab.com:company/repo.git"
    token = "my_secret_token"

    with patch("ikctl.config.git_provider.logging.getLogger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        provider._logger = mock_logger

        result = provider._inject_token(url, token)

    assert result == url
    mock_logger.warning.assert_called_once()
    warning_msg = mock_logger.warning.call_args[0][0]
    assert "SSH" in warning_msg or "ssh" in warning_msg.lower() or "token ignored" in warning_msg


def test_clone_uses_token_url(tmp_path: pathlib.Path) -> None:
    """When kits_token is set, _clone() passes the auth URL to git clone."""
    provider = GitKitsProvider()
    provider.CACHE_DIR = tmp_path  # type: ignore[misc]

    repo_url = "https://gitlab.com/company/private-kits.git"
    token = "secret123"
    ref = "main"

    with patch("ikctl.config.git_provider.subprocess.run") as mock_run:
        mock_run.return_value = _make_completed_process(returncode=0)

        provider.ensure(repo_url, ref, kits_token=token)

    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    auth_url = f"https://oauth2:{token}@gitlab.com/company/private-kits.git"
    assert auth_url in call_args
    assert repo_url not in call_args


def test_clone_censors_token_in_error_message(tmp_path: pathlib.Path) -> None:
    """When git clone fails, the token is replaced with *** in the ConfigError message."""
    provider = GitKitsProvider()
    provider.CACHE_DIR = tmp_path  # type: ignore[misc]

    repo_url = "https://gitlab.com/company/private-kits.git"
    token = "my_secret_token"

    with patch("ikctl.config.git_provider.subprocess.run") as mock_run:
        mock_run.return_value = _make_completed_process(
            returncode=1,
            stderr=f"fatal: could not read Username for 'https://oauth2:{token}@gitlab.com': No such device or address",
        )

        with pytest.raises(ConfigError) as exc_info:
            provider.ensure(repo_url, "main", kits_token=token)

    error_msg = str(exc_info.value)
    assert token not in error_msg
    assert "***" in error_msg


def test_ensure_without_token_unchanged(tmp_path: pathlib.Path) -> None:
    """Without a token, ensure() behaves identically to the original implementation."""
    provider = GitKitsProvider()
    provider.CACHE_DIR = tmp_path  # type: ignore[misc]

    repo_url = "https://gitlab.com/company/kits.git"
    ref = "main"

    with patch("ikctl.config.git_provider.subprocess.run") as mock_run:
        mock_run.return_value = _make_completed_process(returncode=0)

        result = provider.ensure(repo_url, ref, kits_token=None)

    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert repo_url in call_args
    assert "oauth2" not in " ".join(call_args)
    assert result.startswith(str(tmp_path))
