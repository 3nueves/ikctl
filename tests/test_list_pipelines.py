"""Tests for --list pipelines support in view.py and main.py."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

import pytest

from ikctl.view import Show


def _make_show(path_pipelines: str | None = None) -> Show:
    """Returns a Show instance with minimal fixture data and optional path_pipelines."""
    kits = ["my-kit/ikctl.yaml"]
    servers = [
        {"name": "web", "user": "root", "port": 22, "password": "no_pass", "hosts": ["1.2.3.4"]},
    ]
    contexts = {
        "contexts": ["dev"],
        "context": "dev",
    }
    return Show(
        kits=kits,
        path_kits="/path/kits",
        servers=servers,
        path_servers="/path/servers",
        contexts=contexts,
        mode="remote",
        path_secrets="/path/secrets",
        path_pipelines=path_pipelines,
    )


def test_list_pipelines_shows_yaml_files(capsys: pytest.CaptureFixture) -> None:
    """show_config('pipelines') must list .yaml files found in path_pipelines."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline_a = os.path.join(tmpdir, "deploy-app.yaml")
        pipeline_b = os.path.join(tmpdir, "install-docker.yaml")
        for path in (pipeline_a, pipeline_b):
            with open(path, "w", encoding="utf-8") as f:
                f.write("name: test\nsteps: []\n")

        _make_show(path_pipelines=tmpdir).show_config("pipelines")
        captured = capsys.readouterr()

        assert "deploy-app" in captured.out
        assert "install-docker" in captured.out


def test_list_pipelines_no_path_configured(capsys: pytest.CaptureFixture) -> None:
    """show_config('pipelines') with path_pipelines=None must print a clear message, not raise."""
    _make_show(path_pipelines=None).show_config("pipelines")
    captured = capsys.readouterr()

    assert "path_pipelines" in captured.out
    assert "not configured" in captured.out or "configured" in captured.out


def test_list_pipelines_empty_dir(capsys: pytest.CaptureFixture) -> None:
    """show_config('pipelines') with an empty directory must print 'No pipelines found'."""
    with tempfile.TemporaryDirectory() as tmpdir:
        _make_show(path_pipelines=tmpdir).show_config("pipelines")
        captured = capsys.readouterr()

        assert "No pipelines found" in captured.out


def test_main_accepts_list_pipelines_argument() -> None:
    """ikctl --list pipelines must not be rejected by argparse (exit code != 2)."""
    result = subprocess.run(
        [sys.executable, "-m", "ikctl.main", "--list", "pipelines"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 2, (
        f"argparse rejected '--list pipelines' with code 2.\nstderr: {result.stderr}"
    )
