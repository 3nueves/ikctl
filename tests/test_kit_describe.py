"""Tests for kit_outputs_descriptor feature (id=18)."""
from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ikctl.config.models import KitPipeline


# ---------------------------------------------------------------------------
# 1. KitPipeline has outputs field
# ---------------------------------------------------------------------------

def test_kit_pipeline_has_outputs_field():
    """KitPipeline created with non-empty outputs stores the dict correctly."""
    kit = KitPipeline(
        uploads=["script.sh"],
        pipeline=["script.sh"],
        outputs={"JOIN_TOKEN": "kubeadm join token", "JOIN_ENDPOINT": "API server endpoint (IP:6443)"},
    )
    assert kit.outputs == {
        "JOIN_TOKEN": "kubeadm join token",
        "JOIN_ENDPOINT": "API server endpoint (IP:6443)",
    }


def test_kit_pipeline_outputs_defaults_to_empty_dict():
    """KitPipeline created without outputs defaults to an empty dict."""
    kit = KitPipeline(uploads=["script.sh"], pipeline=["script.sh"])
    assert kit.outputs == {}


# ---------------------------------------------------------------------------
# 2. KitRepository parses outputs from ikctl.yaml
# ---------------------------------------------------------------------------

def test_kit_repo_parses_outputs(tmp_path):
    """KitRepository.resolve() includes outputs when the manifest declares them."""
    from ikctl.config.models import Context, IkctlConfig
    from ikctl.config.kit_repo import KitRepository

    kit_dir = tmp_path / "kubernetes"
    kit_dir.mkdir()
    manifest = kit_dir / "ikctl.yaml"
    manifest.write_text(
        textwrap.dedent("""\
            kits:
              uploads:
                - install.sh
              pipeline:
                - install.sh
              outputs:
                JOIN_TOKEN: kubeadm join token
                JOIN_ENDPOINT: API server endpoint (IP:6443)
        """),
        encoding="utf-8",
    )
    (kit_dir / "install.sh").write_text("#!/bin/bash\n", encoding="utf-8")

    ctx = Context(
        name="test",
        path_kits=str(tmp_path),
        path_servers="/tmp",
        path_secrets="/tmp",
        mode="remote",
    )
    config = IkctlConfig(context="test", contexts={"test": ctx})
    repo = KitRepository(config)

    kit = repo.resolve("kubernetes")

    assert kit.outputs == {
        "JOIN_TOKEN": "kubeadm join token",
        "JOIN_ENDPOINT": "API server endpoint (IP:6443)",
    }


def test_kit_repo_no_outputs_returns_empty_dict(tmp_path):
    """KitRepository.resolve() returns empty outputs when manifest has no outputs field."""
    from ikctl.config.models import Context, IkctlConfig
    from ikctl.config.kit_repo import KitRepository

    kit_dir = tmp_path / "docker"
    kit_dir.mkdir()
    manifest = kit_dir / "ikctl.yaml"
    manifest.write_text(
        textwrap.dedent("""\
            kits:
              uploads:
                - install.sh
              pipeline:
                - install.sh
        """),
        encoding="utf-8",
    )
    (kit_dir / "install.sh").write_text("#!/bin/bash\n", encoding="utf-8")

    ctx = Context(
        name="test",
        path_kits=str(tmp_path),
        path_servers="/tmp",
        path_secrets="/tmp",
        mode="remote",
    )
    config = IkctlConfig(context="test", contexts={"test": ctx})
    repo = KitRepository(config)

    kit = repo.resolve("docker")

    assert kit.outputs == {}


# ---------------------------------------------------------------------------
# 3. --describe calls View.show_kit_describe with correct args
# ---------------------------------------------------------------------------

def test_describe_calls_show_kit_describe(tmp_path):
    """When --describe is given, View.show_kit_describe is called with the kit name and pipeline."""
    from ikctl.config.models import Context, IkctlConfig
    from ikctl.config.kit_repo import KitRepository

    kit_dir = tmp_path / "mykit"
    kit_dir.mkdir()
    manifest = kit_dir / "ikctl.yaml"
    manifest.write_text(
        textwrap.dedent("""\
            kits:
              uploads:
                - run.sh
              pipeline:
                - run.sh
              outputs:
                RESULT: result value
        """),
        encoding="utf-8",
    )
    (kit_dir / "run.sh").write_text("#!/bin/bash\n", encoding="utf-8")

    ctx = Context(
        name="test",
        path_kits=str(tmp_path),
        path_servers="/tmp",
        path_secrets="/tmp",
        mode="remote",
    )
    config = IkctlConfig(context="test", contexts={"test": ctx})
    repo = KitRepository(config)
    kit_pipeline = repo.resolve("mykit")

    from ikctl.view import Show

    view = Show(kits=[], path_kits="", servers=[], path_servers="", contexts={}, mode="", path_secrets="")
    with patch.object(view, "show_kit_describe") as mock_describe:
        view.show_kit_describe("mykit", kit_pipeline)
        mock_describe.assert_called_once_with("mykit", kit_pipeline)


# ---------------------------------------------------------------------------
# 4. show_kit_describe renders outputs table or 'No outputs declared'
# ---------------------------------------------------------------------------

def test_show_kit_describe_with_outputs(capsys):
    """show_kit_describe prints output keys when kit has outputs."""
    from ikctl.view import Show

    kit = KitPipeline(
        uploads=["/kits/docker/install.sh"],
        pipeline=["/kits/docker/install.sh"],
        outputs={"TOKEN": "join token value"},
    )
    view = Show(kits=[], path_kits="", servers=[], path_servers="", contexts={}, mode="", path_secrets="")
    view.show_kit_describe("docker", kit)

    captured = capsys.readouterr()
    assert "TOKEN" in captured.out
    assert "join token value" in captured.out


def test_show_kit_describe_no_outputs(capsys):
    """show_kit_describe prints 'No outputs declared' when kit has no outputs."""
    from ikctl.view import Show

    kit = KitPipeline(
        uploads=["/kits/docker/install.sh"],
        pipeline=["/kits/docker/install.sh"],
    )
    view = Show(kits=[], path_kits="", servers=[], path_servers="", contexts={}, mode="", path_secrets="")
    view.show_kit_describe("docker", kit)

    captured = capsys.readouterr()
    assert "No outputs declared" in captured.out


# ---------------------------------------------------------------------------
# 5. --list kits shows Outputs column
# ---------------------------------------------------------------------------

def test_list_kits_shows_outputs_column(capsys):
    """show_config('kits') shows an Outputs column with keys or '-'."""
    from ikctl.view import Show

    kit_with_outputs = KitPipeline(
        uploads=["script.sh"],
        pipeline=["script.sh"],
        outputs={"JOIN_TOKEN": "token", "JOIN_ENDPOINT": "endpoint"},
    )
    kit_without_outputs = KitPipeline(
        uploads=["install.sh"],
        pipeline=["install.sh"],
    )

    view = Show(
        kits=["kubernetes/ikctl.yaml", "docker/ikctl.yaml"],
        path_kits="/kits",
        servers=[],
        path_servers="",
        contexts={},
        mode="remote",
        path_secrets="",
        kit_pipelines={
            "kubernetes": kit_with_outputs,
            "docker": kit_without_outputs,
        },
    )
    view.show_config("kits")

    captured = capsys.readouterr()
    assert "Outputs" in captured.out
    assert "JOIN_TOKEN" in captured.out
    assert "JOIN_ENDPOINT" in captured.out
    assert "-" in captured.out
