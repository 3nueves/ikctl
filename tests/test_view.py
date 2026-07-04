"""Tests for the Show class in view.py."""
from __future__ import annotations

import pytest

from ikctl.view import Show


def _make_show(mode: str = "remote") -> Show:
    """Returns a Show instance with minimal fixture data."""
    kits = ["my-kit/ikctl.yaml", "other-kit/ikctl.yaml"]
    servers = [
        {"name": "web", "user": "root", "port": 22, "password": "secret", "hosts": ["1.2.3.4"]},
    ]
    contexts = {
        "contexts": ["dev", "prod"],
        "context": "dev",
    }
    return Show(
        kits=kits,
        path_kits="/path/kits",
        servers=servers,
        path_servers="/path/servers",
        contexts=contexts,
        mode=mode,
        path_secrets="/path/secrets",
    )


def test_show_config_kits_lists_kit_names(capsys: pytest.CaptureFixture) -> None:
    """show_config('kits') must print each kit name without '/ikctl.yaml' suffix."""
    _make_show().show_config("kits")
    captured = capsys.readouterr()
    assert "my-kit" in captured.out
    assert "other-kit" in captured.out
    assert "/ikctl.yaml" not in captured.out


def test_show_config_context_prints_details(capsys: pytest.CaptureFixture) -> None:
    """show_config('context') must print contexts, mode, paths."""
    _make_show().show_config("context")
    captured = capsys.readouterr()
    assert "dev" in captured.out
    assert "prod" in captured.out
    assert "remote" in captured.out
    assert "/path/kits" in captured.out
    assert "/path/servers" in captured.out
    assert "/path/secrets" in captured.out


def test_show_config_servers_masks_password(capsys: pytest.CaptureFixture) -> None:
    """show_config('servers') must mask the password field."""
    _make_show(mode="remote").show_config("servers")
    captured = capsys.readouterr()
    assert "secret" not in captured.out
    assert "***" in captured.out


def test_show_config_servers_local_mode_skips_listing(capsys: pytest.CaptureFixture) -> None:
    """show_config('servers') in local mode must print the local mode message instead."""
    _make_show(mode="local").show_config("servers")
    captured = capsys.readouterr()
    assert "local" in captured.out


def test_show_config_mode_prints_context(capsys: pytest.CaptureFixture) -> None:
    """show_config('mode') must print the active context name."""
    _make_show().show_config("mode")
    captured = capsys.readouterr()
    assert "dev" in captured.out


def test_show_config_exact_match_not_substring(capsys: pytest.CaptureFixture) -> None:
    """show_config uses exact matching — 'kit' alone must not trigger the kits branch."""
    _make_show().show_config("kit")
    captured = capsys.readouterr()
    assert "local" in captured.out or "mode" in captured.out.lower() or "KIT" in captured.out
    assert "/ikctl.yaml" not in captured.out
